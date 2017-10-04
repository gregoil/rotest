"""Describe resource oriented TestCases."""
# pylint: disable=too-many-public-methods,too-many-arguments
# pylint: disable=too-many-instance-attributes,too-few-public-methods
# pylint: disable=no-member,method-hidden,broad-except,bare-except,invalid-name
import sys
import unittest
from bdb import BdbQuit
from functools import wraps
from itertools import count

from ipdbugger import debug
from attrdict import AttrDict

from rotest.common import core_log
from rotest.common.utils import get_work_dir
from rotest.common.log import get_test_logger
from rotest.common.config import ROTEST_WORK_DIR
from rotest.management.common.errors import ServerError
from rotest.management.client.manager import ResourceRequest
from rotest.core.models.case_data import TestOutcome, CaseData
from rotest.management.client.manager import ClientResourceManager

request = ResourceRequest


class TestCase(unittest.TestCase):
    """Resource oriented :class:`unittest.TestCase`.

    Defines tests that interact with specific resources. The case is
    responsible for locking the required resources before running tests and
    releasing the resources after running all tests in the class using
    :class:`rotest.management.client.manager.ClientResourceManager`.

    Test authors should subclass TestCase for their own tests and override
    'resources' tuple with the required resource descriptors.

    Attributes:
        resources (tuple): list of the required resources. each item is a
            tuple of (resource_name, resource type, parameters dictionary),
            you can use :func:`rotest.core.case.request` to create the tuple.
        data (rotest.core.models.case_data.CaseData): contain information
            about a test case run.
        logger (logging.Logger): test logger.
        identifier (number): unique id of the test.
        work_dir (str): test directory, contains test data and sub-tests.
        save_state (bool): a flag to determine if storing the states of
            resources is required.
        force_validate (bool): a flag to determine if the resource will be
            validated once it requested (even if not marked as dirty).
        config (AttrDict): dictionary of configurations.
        enable_debug (bool): whether to enable entering ipdb debugging mode
            upon any exception in a test statement.
        resource_manager (ClientResourceManager): client resource manager.
        skip_init (bool): True to skip resources initialize and validation.

        TAGS (list): list of tags by which the test may be filtered.
        TIMEOUT (number): timeout for case run, None means no timeout.
        IS_COMPLEX (bool): if this test is complex (may contain sub-tests).
    """
    TIMEOUT = 1800  # 30 min
    SETUP_METHOD_NAME = 'setUp'
    TEARDOWN_METHOD_NAME = 'tearDown'

    resources = ()

    TAGS = []
    IS_COMPLEX = False
    test_methods_names = None

    def __init__(self, indexer=count(), methodName='runTest',
                 base_work_dir=ROTEST_WORK_DIR, save_state=True,
                 force_validate=False, config=None, parent=None, run_data=None,
                 enable_debug=True, resource_manager=None, skip_init=False):
        """Validate & initialize the TestCase.

        Args:
            indexer (iterator): the generator of test indexes.
            methodName (str): name of the test method.
            base_work_dir (str): the base directory of the tests.
            save_state (bool): flag to determine if storing the states of
                resources is required.
            force_validate (bool): a flag to determine if the resource will be
                validated once it requested (even if not marked as dirty).
            config (AttrDict): dictionary of configurations.
            parent (TestSuite): container of this test.
            run_data (RunData): test run data object.
            enable_debug (bool): whether to enable entering ipdb debugging mode
                upon any exception in a test statement.
            resource_manager (ClientResourceManager): tests' client resource
                manager instance, leave None to create a new one for the test.
            skip_init (bool): True to skip resources initialize and validation.

        Raises:
            AttributeError: in case of empty resource tuple.
        """
        if enable_debug is True:
            for method_name in (methodName, self.SETUP_METHOD_NAME,
                                self.TEARDOWN_METHOD_NAME):

                debug(getattr(self, method_name),
                      ignore_exceptions=[KeyboardInterrupt,
                                         unittest.SkipTest,
                                         BdbQuit])

        super(TestCase, self).__init__(methodName)

        self.locked_resources = AttrDict()

        self.skip_reason = None
        self.skip_determined = False

        self._tags = None
        self.result = None
        self.config = config
        self.parent = parent
        self.skip_init = skip_init
        self.save_state = save_state
        self._is_client_local = False
        self.identifier = indexer.next()
        self.enable_debug = enable_debug
        self.force_validate = force_validate
        self.parents_count = self._get_parents_count()

        name = self.get_name(methodName)
        core_log.debug("Initializing %r test-case", name)

        core_log.debug("Creating database entry for %r test-case", name)
        self.work_dir = get_work_dir(base_work_dir, name)
        self.data = CaseData(name=name, run_data=run_data)

        self.logger = get_test_logger(repr(self.data), self.work_dir)
        self.resource_manager = resource_manager

        if self.resource_manager is None:
            self.resource_manager = self.create_resource_manager()
            self._is_client_local = True

        core_log.debug("Initialized %r test-case successfully", name)

    @classmethod
    def get_name(cls, method_name):
        """Return test name.

        Returns:
            str. test name.
        """
        return '.'.join((cls.__name__, method_name))

    def create_resource_manager(self):
        """Create a new resource manager client instance.

        Returns:
            ClientResourceManager. new resource manager client.
        """
        return ClientResourceManager(logger=self.logger)

    @classmethod
    def load_test_method_names(cls):
        """Return all test method names to run.

        Returns:
            list. all test method names to run.
        """
        if cls.test_methods_names is None:
            loader = unittest.loader.TestLoader()
            return loader.getTestCaseNames(cls)

        return cls.test_methods_names

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
        if expression is False:
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
        self.locked_resources.update(resources)
        for name, resource in resources.iteritems():
            setattr(self, name, resource)

    def request_resources(self, resources_to_request, use_previous=False):
        """Lock the requested resources and prepare them for the test.

        Lock the required resources using the resource manager, then assign
        each resource to its requested name, and update the result of the
        chosen resources.

        Args:
            resources_to_request (list): list of resource requests to lock.
            use_previous (bool): whether to use previously locked resources and
                release the unused ones.

        Raises:
             SkipTest: failed to retrieve the resources.
        """
        if len(resources_to_request) == 0:
            # No resources to requested.
            return

        try:
            if not self.resource_manager.is_connected():
                self.resource_manager.connect()

            requested_resources = self.resource_manager.request_resources(
                                            config=self.config,
                                            skip_init=self.skip_init,
                                            use_previous=use_previous,
                                            save_state=self.save_state,
                                            requests=resources_to_request,
                                            base_work_dir=self.work_dir,
                                            force_validate=self.force_validate)

            self.add_resources(requested_resources)

        except ServerError as err:
            self.skipTest(repr(err))

        if self.result is not None:
            self.result.updateResources(self)

    def release_resources(self, dirty):
        """Mark the resources of the case as 'dirty' or 'clean'.

        Args:
            dirty (bool): dirty state to set to the resources.
        """
        if len(self.locked_resources) == 0:
            # No resources were locked.
            return

        self.resource_manager.release_resources(self.locked_resources,
                                                dirty=dirty)

    def _decorate_setup(self, setup_method):
        """Decorate setUp method to handle link skips, and resources requests.

        Args:
            setup_method (method): the original setUp method.

        Returns:
            method. the wrapped setUp method.
        """
        @wraps(setup_method)
        def setup_method_wrapper(*args, **kwargs):
            """setup method wrapper.

            * Locks the required resources for the test.
            * Executes the original setUp method.
            * Upon exception, finalizes the resources.
            """
            skip_reason = self.result.shouldSkip(self)
            if skip_reason is not None:
                self.skipTest(skip_reason)

            self.request_resources(self.resources, use_previous=True)
            try:
                setup_method(*args, **kwargs)
            except:
                self.release_resources(dirty=True)
                raise

        return setup_method_wrapper

    def _decorate_test_method(self, test_method):
        """Decorate testMethod to handle keyboard interrupts.

        Args:
            test_method (method): the original test method.

        Returns:
            method. the wrapped test method.
        """
        @wraps(test_method)
        def test_method_wrapper(*args, **kwargs):
            """test method wrapper.

            Mark any keyboard interrupt that occurs during the test method as a
            'user interrupted' skip.
            The user will see the code which is currently being executed at the
            point of the interruption, and then will be 'redirected' to the
            case scope inside an ipdb, allowing the user to see the current
            state of the case. Then the test is marked as skipped, and
            tearDown is called.
            """
            self.logger.warning('Finished setUp - '
                                'Skipping test is now available')

            try:
                test_method(*args, **kwargs)

            finally:
                self.logger.warning('Starting tearDown - '
                                    'Skipping test is unavailable')

        return test_method_wrapper

    def _decorate_teardown(self, teardown_method, result):
        """Decorate the tearDown method to handle resource release.

        Args:
            test_method (method): the original tearDown method.
            result (rotest.core.result.result.Result): test result information.

        Returns:
            method. the wrapped tearDown method.
        """
        @wraps(teardown_method)
        def teardown_method_wrapper(*args, **kwargs):
            """tearDown method wrapper.

            * Executes the original tearDown method.
            * Releases the test resources.
            """
            try:
                teardown_method(*args, **kwargs)

            except:
                result.addError(self, sys.exc_info())

            finally:
                self.release_resources(
                          dirty=self.data.exception_type == TestOutcome.ERROR)
                if self._is_client_local is True:
                    self.resource_manager.disconnect()

        return teardown_method_wrapper

    def _get_parents_count(self):
        """Get the number of ancestors.

        Returns:
            number. number of ancestors.
        """
        return self.parent.parents_count + 1

    def start(self):
        """Update the data that the test started."""
        self.data.start()

    def end(self, test_outcome, details=None):
        """Update the data that the test ended.

        Args:
            test_outcome (rotest.core.models.case_data.TestOutcome): test
                outcome code.
            details (str): details of the result (traceback/skip reason).
        """
        self.data.update_result(test_outcome, details)

    def run(self, result=None):
        """Run the test case.

        * Decorate setUp method to handle link skips, and resources requests.
        * Decorate testMethod to handle user keyboard interrupts as skips.
        * Decorate the tearDown method to handle resource release.
        * Runs the original run method.

        Args:
            result (rotest.core.result.result.Result): test result information.
        """
        # We set the result default value as None because of the overridden
        # method signature, but the Rotest test case does not support it.
        self.assertIsNotNone(result, 'TestCase must run inside a TestSuite')
        self.result = result

        # === Decorate the setUp, test and tearDown methods. ===
        setup_method = getattr(self, self.SETUP_METHOD_NAME)
        setattr(self, self.SETUP_METHOD_NAME,
                self._decorate_setup(setup_method))

        test_method = getattr(self, self._testMethodName)
        setattr(self, self._testMethodName,
                self._decorate_test_method(test_method))

        teardown_method = getattr(self, self.TEARDOWN_METHOD_NAME)
        setattr(self, self.TEARDOWN_METHOD_NAME,
                self._decorate_teardown(teardown_method, result))

        super(TestCase, self).run(result)
