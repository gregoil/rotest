"""Define resources model classes.

Defines the basic attributes & interface of any resource type class,
responsible for the resource static & dynamic information.
"""
# pylint: disable=too-many-instance-attributes,no-self-use,broad-except
# pylint: disable=protected-access
from __future__ import absolute_import

import sys
from bdb import BdbQuit
from threading import Thread

import six
from ipdbugger import debug
from attrdict import AttrDict
from future.utils import iteritems
from future.builtins import zip, object
from django.db.models.fields.related import \
                                        ReverseSingleRelatedObjectDescriptor

from rotest.common import core_log
from rotest.common.config import ROTEST_WORK_DIR
from rotest.common.utils import get_work_dir, get_class_fields
from rotest.management.models.resource_data import ResourceData, DataPointer


class ResourceRequest(object):
    """Holds the data for a resource request.

    Attributes:
        resource_name (str): attribute name to be assigned.
        resource_class (type): resource type.
        force_initialize (bool): a flag to determine if the resources will be
            initialized even if their validation succeeds.
        kwargs (dict): requested resource arguments.
    """

    def __init__(self, resource_name, resource_class, **kwargs):
        """Initialize the required parameters of resource request."""
        self.name = resource_name
        self.type = resource_class

        self.kwargs = kwargs

    def __eq__(self, oth):
        """Compare with another request."""
        return oth.name == self.name

    def __repr__(self):
        """Return a string representing the request."""
        return "Request %r of type %r (kwargs=%r)" % (self.name, self.type,
                                                      self.kwargs)

    def clone(self):
        """Create a copy of the request."""
        return ResourceRequest(self.name, self.type, **self.kwargs)


class ExceptionCatchingThread(Thread):
    """A thread that saves traceback information if one occurs."""
    def __init__(self, *args, **kwargs):
        super(ExceptionCatchingThread, self).__init__(*args, **kwargs)
        self.traceback_tuple = None

    def run(self):
        try:
            super(ExceptionCatchingThread, self).run()

        except Exception:
            self.traceback_tuple = sys.exc_info()
            raise


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
    """

    DATA_CLASS = None
    PARALLEL_INITIALIZATION = False

    _SHELL_CLIENT = None
    _SHELL_REQUEST_NAME = 'shell_resource'

    def __init__(self, data=None, config=None, base_work_dir=ROTEST_WORK_DIR,
                 **kwargs):
        # We use core_log as default logger in case
        # that resource is used outside case.
        self.logger = core_log
        self._prev_loggers = []

        if data is not None:
            self.data = data
            if isinstance(data, ResourceData):
                for field_name, value in iteritems(self.data.get_fields()):
                    setattr(self, field_name, value)

        else:
            self.data = AttrDict(**kwargs)
            if 'name' not in self.data:
                self.data.name = "%s-%d" % (self.__class__.__name__, id(self))

            for field_name, field_value in iteritems(self.data):
                setattr(self, field_name, field_value)

        self.config = config
        self.parent = None
        self.work_dir = None
        self._sub_resources = None

        self.set_work_dir(self.name, base_work_dir)
        self.logger.debug("Resource %r work dir was created under %r",
                          self.name, base_work_dir)

        self.set_sub_resources()

    @classmethod
    def request(cls, **kwargs):
        """Create a resource request for an instance of this class."""
        return ResourceRequest(None, cls, **kwargs)

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
        for sub_name, sub_request in get_class_fields(self.__class__,
                                                      ResourceRequest):
            sub_class = sub_request.type
            actual_kwargs = sub_request.kwargs.copy()
            actual_kwargs['config'] = self.config
            actual_kwargs['base_work_dir'] = self.work_dir
            for key, value in six.iteritems(sub_request.kwargs):
                if isinstance(value, ReverseSingleRelatedObjectDescriptor):
                    actual_kwargs[key] = getattr(self.data, value.field.name)

                elif isinstance(value, DataPointer):
                    actual_kwargs[key] = getattr(self.data, value.field_name)

            sub_resource = sub_class(**actual_kwargs)

            setattr(self, sub_name, sub_resource)
            sub_resources.append(sub_resource)

        return sub_resources

    def setup_resource(self, skip_init=False, force_initialize=False):
        """Try to initialize the resource.

        Note:
            Initialization failure will cause a finalization attempt.

        Args:
            force_initialize(bool): True to always initialize.
            skip_init (bool): True to skip initialize and validation.
        """
        try:
            self.connect()

        except Exception:
            self.logger.exception("Connecting to %r failed", self.name)
            raise

        if skip_init:
            self.logger.debug("Skipping validation and initialization")
            return

        try:
            self.logger.debug("Initializing resource %r", self.name)
            self._initialize_resource(force_initialize)
            self.logger.debug("Resource %r was initialized", self.name)

        except Exception:
            self.logger.exception("Failed initializing %r, calling finalize",
                                  self.name)
            self.finalize()
            raise

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

    def _initialize_resource(self, force_initialize=False):
        """Validate and initialize if needed the resource and subresources."""
        sub_threads = []
        for sub_resource in self.get_sub_resources():
            if self.PARALLEL_INITIALIZATION:
                sub_resource.logger.debug("Initializing %r in a new thread",
                                          sub_resource.name)

                initialize_thread = ExceptionCatchingThread(
                                    target=sub_resource._initialize_resource,
                                    args=(force_initialize,))

                initialize_thread.start()
                sub_threads.append(initialize_thread)

            else:
                sub_resource._initialize_resource(force_initialize)

        for sub_thread, sub_resource in zip(sub_threads,
                                            self.get_sub_resources()):

            sub_thread.join()
            if sub_thread.traceback_tuple is not None:
                self.logger.error("Got an error while preparing resource %s",
                                  sub_resource.name,
                                  exc_info=sub_thread.traceback_tuple)

        for sub_thread in sub_threads:
            if sub_thread.traceback_tuple is not None:
                six.reraise(*sub_thread.traceback_tuple)

        if force_initialize or not self.validate():
            if not force_initialize:
                self.logger.debug("Resource %r validation failed",
                                  self.name)

            self.initialize()

        else:
            self.logger.debug("Resource %r skipped initialization",
                              self.name)

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
        from rotest.management.client.manager import ClientResourceManager

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
