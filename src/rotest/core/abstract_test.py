"""Describe TestBlock class."""
# pylint: disable=attribute-defined-outside-init,unused-argument
# pylint: disable=dangerous-default-value,access-member-before-definition
# pylint: disable=bare-except,protected-access,too-many-instance-attributes
# pylint: disable=too-many-arguments,too-many-locals,broad-except,no-self-use
# pylint: disable=too-many-public-methods,deprecated-method
from __future__ import absolute_import

import os
import sys
import unittest
import platform
from bdb import BdbQuit
from functools import wraps
from itertools import count

from ipdbugger import debug
from attrdict import AttrDict
from cached_property import cached_property
from future.builtins import next, str, object
from future.utils import iteritems, itervalues

from rotest.core.result.result import Result
from rotest.common.utils import get_class_fields
from rotest.core.models.case_data import TestOutcome
from rotest.management.base_resource import ResourceRequest
from rotest.common.log import get_test_logger, get_tree_path
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

    resources = ()

    TAGS = []
    IS_COMPLEX = False

    STATE_DIR_NAME = "state"

    def __init__(self, methodName='test_method', indexer=count(), parent=None,
                 save_state=True, force_initialize=False, config=None,
                 enable_debug=False, resource_manager=None, skip_init=False):

        if enable_debug:
            for method_name in (methodName, self.SETUP_METHOD_NAME,
                                self.TEARDOWN_METHOD_NAME):

                debug(getattr(self, method_name),
                      ignore_exceptions=[KeyboardInterrupt,
                                         unittest.SkipTest,
                                         BdbQuit])

        super(AbstractTest, self).__init__(methodName)

        self.result = None
        self.is_main = True
        self.config = config
        self.parent = parent
        self.skip_init = skip_init
        self.save_state = save_state
        self.identifier = next(indexer)
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
        for resource in itervalues(self.all_resources):
            resource.override_logger(self.logger)

    def release_resource_loggers(self):
        """Revert logger replacement."""
        for resource in itervalues(self.all_resources):
            resource.release_logger(self.logger)

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
        for (field_name, new_request) in get_class_fields(cls,
                                                          ResourceRequest):

            new_request.name = field_name
            if new_request not in all_requests:
                all_requests.append(new_request)

        return all_requests

    def create_resource_manager(self):
        """Create a new resource manager client instance.

        Returns:
            ClientResourceManager. new resource manager client.
        """
        return ClientResourceManager()

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
        for name, resource in iteritems(resources):
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
                                        base_work_dir=self.work_dir,
                                        requests=resources_to_request,
                                        enable_debug=self.enable_debug,
                                        force_initialize=self.force_initialize)

        self.add_resources(requested_resources)
        self.locked_resources.update(requested_resources)
        for resource in itervalues(requested_resources):
            resource.override_logger(self.logger)

        if isinstance(self.result, Result):
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
            resources = list(self.locked_resources.keys())

        if len(resources) == 0:
            # No resources to release locked
            return

        resources_dict = {
            name: resource
            for name, resource in iteritems(self.locked_resources)
            if name in resources
        }

        self.resource_manager.release_resources(resources_dict,
                                                dirty=dirty,
                                                force_release=force_release)

        # Remove the resources from the test's resource to avoid double release
        for resource in itervalues(resources_dict):
            self.locked_resources.pop(resource, None)

    def _get_parents_count(self):
        """Get the number of ancestors.

        Returns:
            number. number of ancestors.
        """
        if self.parent is None:
            return 0

        return self.parent.parents_count + 1

    @cached_property
    def logger(self):
        """Create logger instance for the test."""
        return get_test_logger(get_tree_path(self), self.work_dir)

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

    def _decorate_teardown(self, teardown_method):
        """Decorate the tearDown method to handle resource release.

        Args:
            teardown_method (function): the original tearDown method.

        Returns:
            function. the wrapped tearDown method.
        """
        @wraps(teardown_method)
        def teardown_method_wrapper(*args, **kwargs):
            """tearDown method wrapper.

            * Executes the original tearDown method.
            * Releases the test resources.
            * Closes the client if needed
            """
            if isinstance(self.result, Result):
                self.result.startTeardown(self)

            try:
                teardown_method(*args, **kwargs)

            except Exception:
                self.result.addError(self, sys.exc_info())

            finally:
                self.store_state()
                self.release_resources(
                       dirty=self.data.exception_type == TestOutcome.ERROR,
                       force_release=False)

                if (self._is_client_local and
                        self.resource_manager.is_connected()):
                    self.resource_manager.disconnect()

        return teardown_method_wrapper

    def store_state(self):
        """Store the state of the resources in the work dir."""
        # In Python 3 tearDown() is called before result.addError() whereas
        # in python 2 addError() is called before tearDown().
        # in python 3 self.data.exception_type would always be None
        # but we could check the error state via the self._outcome object
        # and in python2 we could just check the exception_type identifier.
        if not self.save_state:
            self.logger.debug("Skipping saving state")
            return

        if platform.python_version().startswith("3"):
            exceptions_that_occurred = len([test
                                          for test, exc_info
                                          in self._outcome.errors
                                          if exc_info is not None])

            if exceptions_that_occurred == 0:
                self.logger.debug("State is not an errored state, "
                                  "skipping saving state")
                return

        elif platform.python_version().startswith("2"):
            status = self.data.exception_type
            if status is None or status in TestOutcome.POSITIVE_RESULTS:
                self.logger.debug("State is not an errored state, "
                                  "skipping saving state")
                return

        store_dir = os.path.join(self.work_dir, self.STATE_DIR_NAME)

        # In case a state dir already exists, create a new one.
        state_dir_index = 1
        while os.path.exists(store_dir):
            state_dir_index += 1
            store_dir = os.path.join(self.work_dir,
                                     self.STATE_DIR_NAME + str(
                                         state_dir_index))

        self.logger.debug("Creating state dir %r", store_dir)
        os.makedirs(store_dir)

        for resource in itervalues(self.locked_resources):
            resource.store_state(store_dir)

    def _wrap_assert(self, assert_method, *args, **kwargs):
        try:
            assert_method(*args, **kwargs)

        except AssertionError as err:
            self.expect(False, str(err))

    class _ExpectRaisesContext(object):
        def __init__(self, assert_context, wrap_assert):
            self.assert_context = assert_context
            self.wrap_assert = wrap_assert

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, tb):
            self.wrap_assert(self.assert_context.__exit__,
                             exc_type, exc_value, tb)

    def expectRaises(self, expected_exception, callable_obj=None,
                     *args, **kwargs):

        if callable_obj is None:
            return AbstractTest._ExpectRaisesContext(self.assertRaises(
                                                        expected_exception,
                                                        callable_obj,
                                                        *args, **kwargs),
                                                     self._wrap_assert)

        self._wrap_assert(self.assertRaises, expected_exception, callable_obj,
                          *args, **kwargs)

    def expectRaisesRegexp(self, expected_exception, expected_regexp,
                           callable_obj=None, *args, **kwargs):

        if callable_obj is None:
            return AbstractTest._ExpectRaisesContext(self.assertRaisesRegexp(
                                                        expected_exception,
                                                        expected_regexp,
                                                        callable_obj,
                                                        *args, **kwargs),
                                                     self._wrap_assert)

        self._wrap_assert(self.assertRaisesRegexp, expected_exception,
                          expected_regexp, callable_obj, *args, **kwargs)

    def addSuccess(self, msg):
        """Register a success message to the test result.

        Args:
            msg (str): success message to add to the result.
        """
        self.result.addSuccess(self, msg)

    # Shortcuts
    success = addSuccess
    skip = unittest.TestCase.skipTest


def create_expect_method(method_name):
    original_assert = getattr(unittest.TestCase, method_name)
    @wraps(original_assert)
    def extended_assert(self, *args, **kwargs):
        success_msg = kwargs.pop("success_msg", None)
        retval = original_assert(self, *args, **kwargs)
        if success_msg is not None:
            self.success(success_msg)
        return retval

    setattr(AbstractTest, method_name, extended_assert)

    def expect_func(self, *args, **kwargs):
        return self._wrap_assert(getattr(self, method_name), *args, **kwargs)

    expect_func.__doc__ = """Like {} but doesn't break workflow.""".format(
                                                                method_name)

    setattr(AbstractTest, method_name.replace("assert", "expect"),
            expect_func)


# Create an 'expect' method for every 'assert' method in unittest.TestCase
for attr_name in unittest.TestCase.__dict__:
    if attr_name.startswith("assert") and \
            "Raises" not in attr_name and "_" not in attr_name:

        create_expect_method(attr_name)
