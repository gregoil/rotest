"""Describe TestBlock class."""
# pylint: disable=attribute-defined-outside-init,unused-argument
# pylint: disable=too-many-arguments,too-many-locals,broad-except
# pylint: disable=dangerous-default-value,access-member-before-definition
# pylint: disable=bare-except,protected-access,too-many-instance-attributes
import unittest
from bdb import BdbQuit
from itertools import count

from ipdbugger import debug
from attrdict import AttrDict

from rotest.management.base_resource import BaseResource
from rotest.management.client.manager import ResourceRequest
from rotest.management.client.manager import ClientResourceManager


request = ResourceRequest


class AbstractTest(unittest.TestCase):
    """Base class for all runnable Rotest tests.

    Attributes:
        resources (tuple): list of the required resources. each item is a
            tuple of (resource_name, resource type, parameters dictionary),
            you can use :func:`rotest.core..request` to create the tuple.
        identifier (number): unique id of the test.
        data (rotest.core.models._data.Data): contain information
            about a test  run.
        logger (logging.Logger): test logger.
        save_state (bool): a flag to determine if storing the states of
            resources is required.
        force_initialize (bool): a flag to determine if the resources will be
            initialized even if their validation succeeds.
        config (AttrDict): dictionary of configurations.
        enable_debug (bool): whether to enable entering ipdb debugging mode
            upon any exception in a test statement.
        skip_init (bool): True to skip resources initialize and validation.
        resource_manager (ClientResourceManager): client resource manager.
        TAGS (list): list of tags by which the test may be filtered.
        IS_COMPLEX (bool): if this test is complex (may contain sub-tests).
        TIMEOUT (number): timeout for flow run, None means no timeout.
    """
    SETUP_METHOD_NAME = 'setUp'
    TEARDOWN_METHOD_NAME = 'tearDown'

    TIMEOUT = 1800  # 30 minutes
    SETUP_METHOD_NAME = 'setUp'
    TEARDOWN_METHOD_NAME = 'tearDown'

    resources = ()

    TAGS = []
    IS_COMPLEX = False

    def __init__(self, indexer=count(), methodName='runTest', save_state=True,
                 force_initialize=False, config=None, parent=None,
                 enable_debug=True, resource_manager=None, skip_init=False):

        if enable_debug:
            for method_name in (methodName, self.SETUP_METHOD_NAME,
                                self.TEARDOWN_METHOD_NAME):

                debug(getattr(self, method_name),
                      ignore_exceptions=[KeyboardInterrupt,
                                         unittest.SkipTest,
                                         BdbQuit])

        super(AbstractTest, self).__init__(methodName)

        self.result = None
        self.config = config
        self.parent = parent
        self.skip_init = skip_init
        self.save_state = save_state
        self.identifier = indexer.next()
        self.enable_debug = enable_debug
        self.force_initialize = force_initialize
        self.parents_count = self._get_parents_count()

        self.all_resources = AttrDict()
        self.locked_resources = AttrDict()

        self._is_client_local = False
        self.resource_manager = resource_manager

        if parent is not None:
            parent.addTest(self)

    def override_resource_loggers(self):
        """Replace the resources' logger with the test's logger."""
        for resource in self.all_resources.itervalues():
            resource.override_logger(self.logger)

    def release_resource_loggers(self):
        """Revert logger replacement."""
        for resource in self.all_resources.itervalues():
            resource.release_logger(self.logger)

    @classmethod
    def get_resource_requests_fields(cls):
        """Yield tuples of all the resource request fields of this test.

        Yields:
            tuple. (requests name,  request field) tuples of the test class.
        """
        checked_class = cls
        while checked_class is not AbstractTest:
            for field_name in checked_class.__dict__:
                if not field_name.startswith("_"):
                    field = getattr(checked_class, field_name)
                    if isinstance(field, BaseResource):
                        yield (field_name, field)

            checked_class = checked_class.__bases__[0]

    @classmethod
    def get_resource_requests(cls):
        """Return a list of all the resource requests this test makes.

        Resource requests can be done both by overriding the class's
        'resources' field and by declaring class fields that point to a
        BaseResource instance.

        Returns:
            list. resource requests of the test class.
        """
        all_requests = list(cls.resources)
        for (field_name, field) in cls.get_resource_requests_fields():
            new_request = request(field_name,
                                  field.__class__,
                                  **field.kwargs)

            if new_request not in all_requests:
                all_requests.append(new_request)

        return all_requests

    def create_resource_manager(self):
        """Create a new resource manager client instance.

        Returns:
            ClientResourceManager. new resource manager client.
        """
        return ClientResourceManager(logger=self.logger)

    def expect(self, expression, msg=None):
        """Check an expression and fail the test at the end if it's False.

        This does not raise an AssertionError like assertTrue, but instead
        updates the result of the test and appends the message to the saved
        traceback without stopping its flow.

        Args:
            expression (bool): value to validate.
            msg (str): failure message if the expression is False.

        Returns:
            bool. True if the validation passed, False otherwise.
        """
        if not expression:
            failure = AssertionError(msg)
            self.result.addFailure(self, (failure.__class__, failure, None))
            return False

        return True

    def add_resources(self, resources):
        """Register the resources to the case and set them as its attributes.

        Args:
            resources (dict): dictionary of attributes name to resources
                instance.
        """
        self.all_resources.update(resources)
        for name, resource in resources.iteritems():
            setattr(self, name, resource)

    def request_resources(self, resources_to_request, use_previous=False):
        """Lock the requested resources and prepare them for the test.

        Lock the required resources using the resource manager, then assign
        each resource to its requested name, and update the result of the
        chosen resources. This method can also be used to add resources to all
        the sibling blocks under the test-flow.

        Args:
            resources_to_request (list): list of resource requests to lock.
            use_previous (bool): whether to use previously locked resources and
                release the unused ones.
        """
        if len(resources_to_request) == 0:
            # No resources to requested
            return

        requested_resources = self.resource_manager.request_resources(
                                        config=self.config,
                                        skip_init=self.skip_init,
                                        use_previous=use_previous,
                                        save_state=self.save_state,
                                        base_work_dir=self.work_dir,
                                        requests=resources_to_request,
                                        enable_debug=self.enable_debug,
                                        force_initialize=self.force_initialize)

        self.add_resources(requested_resources)
        self.locked_resources.update(requested_resources)
        for resource in requested_resources.itervalues():
            resource.override_logger(self.logger)

        if self.result is not None:
            self.result.updateResources(self)

    def release_resources(self, resources=None, dirty=False,
                          force_release=True):
        """Release given resources using the client.

        Args:
            resources (list): resource names to release, leave None to release
                all locked resources.
            dirty (bool): True if the resource's integrity has been
                compromised, and it should be re-validated.
            force_release (bool): whether to always release to resources
                or enable saving them for next tests.
        """
        if resources is None:
            resources = self.locked_resources.keys()

        if len(resources) == 0:
            # No resources to release locked
            return

        resources_dict = {name: resource
                          for name, resource in self.locked_resources.items()
                          if name in resources}

        self.resource_manager.release_resources(resources_dict,
                                                dirty=dirty,
                                                force_release=force_release)

        # Remove the resources from the test's resource to avoid double release
        for resource in resources_dict.itervalues():
            self.locked_resources.pop(resource, None)

    def _get_parents_count(self):
        """Get the number of ancestors.

        Returns:
            number. number of ancestors.
        """
        if self.parent is None:
            return 0

        return self.parent.parents_count + 1

    def start(self):
        """Update the data that the test started."""
        self.data.start()

    def end(self, test_outcome, details=None):
        """Update the data that the test ended.

        Args:
            test_outcome (number): test outcome code (as defined in
                rotest.core.models.case_data.TestOutcome).
            details (str): details of the result (traceback/skip reason).
        """
        self.data.update_result(test_outcome, details)
