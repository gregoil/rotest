"""Define resources model classes.

Defines the basic attributes & interface of any resource type class,
responsible for the resource static & dynamic information.
"""
# pylint: disable=invalid-name,cell-var-from-loop,broad-except
# pylint: disable=access-member-before-definition,property-on-old-class
# pylint: disable=no-self-use,too-many-public-methods,too-few-public-methods
import os
from bdb import BdbQuit

from ipdbugger import debug

from rotest.common import core_log
from rotest.common.utils import get_work_dir
from rotest.management.common.utils import HOST_PORT_SEPARATOR


class BaseResource(object):
    """Represent the common interface of all the resources.

    To implement a resource, you may override:
    initialize, connect, finalize, reset, validate, create_sub_resources,
    store_state. Also, assign a data container class by setting the
    attribute 'DATA_CLASS', which should point to a subclass of
    :class:`rotest.management.models.resource_data.ResourceData`.

    Attributes:
        DATA_CLASS (class): class of the resource's global data container.
        logger (logger): resource's logger instance.
        data (ResourceData): assigned data instance.
        config (AttrDict): run configuration.
        work_dir (str): working directory for this resource.
        save_state (bool): flag to indicate if the resource is a duplication.
        force_validate (bool): flag to indicate if the validation is mandatory.
    """
    DATA_CLASS = NotImplemented

    _SHELL_CLIENT = None
    _SHELL_REQUEST_NAME = 'shell_resource'

    def __init__(self, data=None):
        # We use core_log as default logger in case
        # that resource is used outside case.
        self.logger = core_log

        self.data = data
        self.config = None
        self.work_dir = None
        self.save_state = None
        self.force_validate = None

        self._sub_resources = None

        # Copy all the resource data's fields to the resource.
        if self.data is not None:
            for field_name, field_value in self.data.get_fields().iteritems():
                setattr(self, field_name, field_value)

    def create_sub_resources(self):
        """Create and return the sub resources if needed.

        Override and assign sub-resources to fields in the current resource,
        using the 'data' object.

        Returns:
            iterable. sub-resources created.
        """
        return ()

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
            user_name = user_name.split(HOST_PORT_SEPARATOR)[0]
            return self.reserved in [user_name, ""] and self.owner == ""

        return leaf.is_available(user_name)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.data)

    def get_sub_resources(self):
        """Return an iterable to the resource's sub-resources."""
        return (sub_resource for sub_resource in self._sub_resources
                if sub_resource.data is not None)

    def set_sub_resources(self):
        """Create and set the sub resources if needed."""
        self._sub_resources = tuple(self.create_sub_resources())
        for resource in self.get_sub_resources():
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
                self.logger.warning("%s failed (reason: %s)",
                                    callback, ex)
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
        self.work_dir = get_work_dir(containing_work_dir, resource_name)

        for resource in self.get_sub_resources():
            resource.set_work_dir(resource.name, self.work_dir)

    def store_state(self, state_dir_path):
        """Hook method for backing up the resource state.

        Args:
            state_dir_path (str): path of state directory to be saved.
        """
        self._safe_execute([resource.store_state_dir for resource
                            in self.get_sub_resources()], state_dir_path)

    def store_state_dir(self, dir_name):
        """Store the resource state under a sub-directory of the work_dir.

        Create a directory under the resource work directory and calls
        store_state on that directory.

        Args:
            dir_name (str): sub-directory name.
        """
        store_dir = os.path.join(self.work_dir, dir_name)
        self.logger.debug("Creating dir %r", store_dir)

        # In case a state dir already exists, create a new one.
        state_dir_index = 1
        while os.path.exists(store_dir) is True:
            state_dir_index += 1
            store_dir = os.path.join(self.work_dir,
                                     dir_name + str(state_dir_index))

        os.makedirs(store_dir)

        self.logger.debug("Storing resource %r state", self.name)
        self.store_state(store_dir)
        self.logger.debug("Resource %r state stored", self.name)

    def initialize(self):
        """Hook method for setting up the resource before using it.

        Will be called by the resource client once the connection to the
        resource was successful. Override to specify the resource's
        initialization procedure (remember to call 'super' at the beginning).
        """
        self.logger.debug("Initializing resource %r", self.name)

        for resource in self.get_sub_resources():
            resource.initialize()

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
        """Boolean Hook method for validating resource state before using it.

        Will be called by the resource client once the resource is locked.

        Returns:
            bool. True if validation succeeded, False otherwise.
        """
        result = True

        for resource in self.get_sub_resources():
            try:
                resource.data.dirty = not resource.validate()

            except Exception:
                resource.data.dirty = True

            result = result and (not resource.data.dirty)

        return result

    def reset(self):
        """Hook method for reseting the resource.

        Will be called by the resource client once a dirty resource is locked.
        """
        dirty_resources = [resource for resource in self.get_sub_resources()
                           if resource.data.dirty is True]

        self._safe_execute([resource.reset for resource in dirty_resources])

    def enable_debug(self):
        """Wrap the resource methods with debugger."""
        debug(self.initialize, ignore_exceptions=[KeyboardInterrupt, BdbQuit])
        debug(self.finalize, ignore_exceptions=[KeyboardInterrupt, BdbQuit])
        debug(self.validate, ignore_exceptions=[KeyboardInterrupt, BdbQuit])
        debug(self.reset, ignore_exceptions=[KeyboardInterrupt, BdbQuit])
        debug(self.store_state, ignore_exceptions=[KeyboardInterrupt, BdbQuit])
        for resource in self.get_sub_resources():
            resource.enable_debug()

    @classmethod
    def lock(cls, skip_init=False, **kwargs):
        """Lock an instance of this resource class.

        Args:
            skip_init (bool): whether to skip initialization or not.
            kwargs (dict): additional query parameters for the request,
                e.g. name or group.

        Returns:
            BaseResource. locked and initialized resource, ready for work.
        """
        from rotest.management.client.manager import (ClientResourceManager,
                                                      ResourceRequest)

        if BaseResource._SHELL_CLIENT is None:
            BaseResource._SHELL_CLIENT = ClientResourceManager()
            BaseResource._SHELL_CLIENT.connect()

        resource_request = ResourceRequest(BaseResource._SHELL_REQUEST_NAME,
                                           cls,
                                           **kwargs)

        result = BaseResource._SHELL_CLIENT.request_resources(
                                                        [resource_request],
                                                        skip_init=skip_init,
                                                        use_previous=False)

        return result[BaseResource._SHELL_REQUEST_NAME]

    def release(self):
        """Release the resource, assuming it was locked with a shell client."""
        if BaseResource._SHELL_CLIENT is not None:
            BaseResource._SHELL_CLIENT.release_resources(
                {BaseResource._SHELL_CLIENT: self},
                force_release=True)
