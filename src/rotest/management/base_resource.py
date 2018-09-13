"""Define resources model classes.

Defines the basic attributes & interface of any resource type class,
responsible for the resource static & dynamic information.
"""
# pylint: disable=too-many-instance-attributes,no-self-use,broad-except
from bdb import BdbQuit

from ipdbugger import debug
from attrdict import AttrDict

from rotest.common import core_log
from rotest.common.utils import get_work_dir, get_class_fields
from rotest.management.models.resource_data import ResourceData


class ConvertToKwargsMeta(type):
    """Metaclass that validates no positional args are passed to constructor.

    This enables avoiding requesting resources is coherent, i.e.:
        Assuming ResClass gets 'x' in the __init__, then when requesting:
            res1 = ResClass(5)
        The x=5 is not passed to kwargs, thus is not propagated when
        creating the actual resource when the test starts.
    """
    def __call__(cls, *args, **kwargs):
        if len(args) > 0:
            raise RuntimeError("BaseResource constructors must not get "
                               "positional arguments")

        resource = type.__call__(cls, *args, **kwargs)
        resource.kwargs = kwargs
        for field_name, field_value in kwargs.iteritems():
            setattr(resource, field_name, field_value)

        if isinstance(resource.data, AttrDict):
            resource.data.update(kwargs)

        return resource


class BaseResource(object):
    """Represent the common interface of all the resources.

    To implement a resource, you may override:
    initialize, connect, finalize, validate, create_sub_resources, store_state.
    Also, assign a data container class by setting the
    attribute 'DATA_CLASS', which should point to a subclass of
    :class:`rotest.management.models.resource_data.ResourceData`.
    Resource without a data class (also called 'Services') will be handled
    locally, without involving the server.

    Attributes:
        DATA_CLASS (class): class of the resource's global data container.
        PARALLEL_INITIALIZATION (bool): whether or not to validate and
            initialize sub-resources in other threads.
        logger (logger): resource's logger instance.
        data (ResourceData): assigned data instance.
        config (AttrDict): run configuration.
        work_dir (str): working directory for this resource.
        force_initialize (bool): a flag to determine if the resource will be
            initialized even if the validation succeeds.
    """
    __metaclass__ = ConvertToKwargsMeta

    DATA_CLASS = None
    PARALLEL_INITIALIZATION = False

    _SHELL_CLIENT = None
    _SHELL_REQUEST_NAME = 'shell_resource'

    def __init__(self, data=None, **kwargs):
        # We use core_log as default logger in case
        # that resource is used outside case.
        self.kwargs = kwargs
        self.logger = core_log
        self._prev_loggers = []

        if data is not None and isinstance(data, ResourceData):
            self.data = data
            for field_name, field_value in self.data.get_fields().iteritems():
                setattr(self, field_name, field_value)

        else:
            self.data = AttrDict()
            self.name = "%s-%d" % (self.__class__.__name__, id(self))
            self.data.name = self.name

        self.config = None
        self.parent = None
        self.work_dir = None
        self.force_initialize = None

        self._sub_resources = None

    def create_sub_resources(self):
        """Create and return the sub resources if needed.

        By default, this method searches for sub-resources declared as
        class fields, where the 'data' attribute in the declaration points
        to the name of the sub-resource's data field under the current's data.

        Override and assign sub-resources to fields in the current resource,
        using the 'data' object.

        Returns:
            iterable. sub-resources created.
        """
        sub_resources = []
        for sub_name, sub_placeholder in get_class_fields(self.__class__,
                                                          BaseResource):

            sub_class = sub_placeholder.__class__
            if sub_class.DATA_CLASS is None:
                sub_data = None

            else:
                sub_data = getattr(self.data, sub_placeholder.data)

            sub_resource = sub_class(data=sub_data, **sub_placeholder.kwargs)

            setattr(self, sub_name, sub_resource)
            sub_resources.append(sub_resource)

        return sub_resources

    def is_available(self, user_name=""):
        """Return whether resource is available for the given user.

        Args:
            user_name (str): user name to be checked. Empty string means
                available to all.

        Returns:
            bool. determine whether resource is available for the given user.

        Note:
            If this method is called from code then leaf is equal to 'self'.
            If it is being called by BaseResources table in DB then leaf's
            'is_available' method will be called.
        """
        leaf = self.leaf  # 'leaf' is a property.
        if leaf == self:
            return self.reserved in [user_name, ""] and self.owner == ""

        return leaf.is_available(user_name)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.data)

    def get_sub_resources(self):
        """Return an iterable to the resource's sub-resources."""
        return (sub_resource for sub_resource in self._sub_resources)

    def set_sub_resources(self):
        """Create and set the sub resources if needed."""
        self._sub_resources = tuple(self.create_sub_resources())
        for resource in self.get_sub_resources():
            resource.parent = self
            resource.set_sub_resources()

    def _safe_execute(self, callbacks, *args, **kwargs):
        """Executes all the callbacks, even if one or more fails.

        Args:
            callbacks (list): callbacks to be called one after the other (even
                if one of them fails).
            args (list): args passed for each callback when invoked.
            kwargs (dict): keyword-args passed for each callback when invoked.

        Raises:
            RuntimeError: when one, or more, of the callbacks fail.
        """
        error_messages = []
        for callback in callbacks:
            try:
                self.logger.debug("Starting %s", callback)
                callback(*args, **kwargs)
                self.logger.debug("%s ended successfully", callback)

            except Exception as ex:
                self.logger.exception("%s failed", callback)
                error_messages.append("%s: %s" % (callback, ex))

        if len(error_messages) != 0:
            raise RuntimeError("Some of the callbacks have failed. "
                               "Reasons: %s" % "\n".join(error_messages))

    def set_work_dir(self, resource_name, containing_work_dir):
        """Set the work directory under the given case's work directory.

        Args:
            resource_name (str): name of resource.
            containing_work_dir (str): root work directory.
        """
        self.work_dir = get_work_dir(containing_work_dir, resource_name, None)

        for resource in self.get_sub_resources():
            resource.set_work_dir(resource.name, self.work_dir)

    def store_state(self, state_dir_path):
        """Hook method for backing up the resource state.

        Args:
            state_dir_path (str): path of state directory to be saved.
        """
        self.logger.debug("Storing resource %r state", self.name)
        self._safe_execute([resource.store_state for resource
                            in self.get_sub_resources()], state_dir_path)

    def initialize(self):
        """Hook method for setting up the resource before using it.

        Will be called by the resource client once the connection to the
        resource was successful. Override to specify the resource's
        initialization procedure (remember to call 'super' at the beginning).
        """
        self.logger.debug("Initializing resource %r", self.name)

    def connect(self):
        """Setup a connection session to the resource.

        Will be called by the resource client once the
        resource is locked successfully.
        """
        self.logger.debug("Connecting resource %r", self.name)

        for resource in self.get_sub_resources():
            resource.connect()

    def finalize(self):
        """Hook method for cleaning up the resource after using it.

        Will be called by the resource client before the resource is released.
        Override to specify the resource's finalization procedure
        (remember to call 'super' at the end).
        """
        # Create a list of resources finalize calls in a specific order.
        self.logger.debug("Finalizing resource %r", self.name)
        finalization_methods = [resource.finalize for resource
                                in self.get_sub_resources()]
        self._safe_execute(finalization_methods)

    def validate(self):
        """Validate whether the resource is ready for work or not.

        If this method failed, the resource client will call the 'initialize'
        method to setup the resource.

        Returns:
            bool. True if validation succeeded, False otherwise.
        """
        return False

    def override_logger(self, new_logger):
        """Replace the resource's logger.

        Args:
            new_logger (logging.Logger): new logger to set.
        """
        if self.logger is new_logger:
            return

        self._prev_loggers.insert(0, self.logger)
        self.logger = new_logger

    def release_logger(self, logger):
        """Revert logger replacement.

        Args:
            logger (logging.Logger): logger to release.
        """
        if self.logger is logger:
            self.logger = self._prev_loggers.pop(0)

    def enable_debug(self):
        """Wrap the resource methods with debugger."""
        debug(self.connect, ignore_exceptions=[KeyboardInterrupt, BdbQuit])
        debug(self.initialize, ignore_exceptions=[KeyboardInterrupt, BdbQuit])
        debug(self.finalize, ignore_exceptions=[KeyboardInterrupt, BdbQuit])
        debug(self.validate, ignore_exceptions=[KeyboardInterrupt, BdbQuit])
        debug(self.store_state, ignore_exceptions=[KeyboardInterrupt, BdbQuit])
        for resource in self.get_sub_resources():
            resource.enable_debug()

    @classmethod
    def lock(cls, config=None, skip_init=False, **kwargs):
        """Lock an instance of this resource class.

        Args:
            config (str): path to the json config file.
            skip_init (bool): whether to skip initialization or not.
            kwargs (dict): additional query parameters for the request,
                e.g. name or group.

        Returns:
            BaseResource. locked and initialized resource, ready for work.
        """
        # These runtime imports are done to avoid cyclic imports.
        from rotest.core.runner import parse_config_file
        from rotest.management.client.manager import (ClientResourceManager,
                                                      ResourceRequest)

        if BaseResource._SHELL_CLIENT is None:
            BaseResource._SHELL_CLIENT = ClientResourceManager()

        resource_request = ResourceRequest(BaseResource._SHELL_REQUEST_NAME,
                                           cls,
                                           **kwargs)

        config_dict = None
        if config is not None:
            config_dict = parse_config_file(config)

        result = BaseResource._SHELL_CLIENT.request_resources(
                                                        [resource_request],
                                                        config=config_dict,
                                                        skip_init=skip_init,
                                                        use_previous=False)

        return result[BaseResource._SHELL_REQUEST_NAME]

    def release(self):
        """Release the resource, assuming it was locked with a shell client."""
        if BaseResource._SHELL_CLIENT is not None:
            BaseResource._SHELL_CLIENT.release_resources(
                {BaseResource._SHELL_REQUEST_NAME: self},
                force_release=True)
