"""Test utils for Rotest UT."""
# pylint: disable=expression-not-assigned,bad-builtin
# pylint: disable=no-self-use,too-many-public-methods,unused-argument
import unittest

import django
from django.db import connections
from django.core.exceptions import ObjectDoesNotExist
from django.test.testcases import TransactionTestCase

from rotest.core.flow import TestFlow
from rotest.core.block import TestBlock
from rotest.core.suite import TestSuite
from rotest.core.result.result import Result
from rotest.core.runner import BaseTestRunner
from rotest.core.case import TestCase, request
from rotest.management.models.ut_models import DemoResource
from rotest.management.client.manager import ClientResourceManager
from rotest.management.common.errors import (ResourceDoesNotExistError,
                                             ResourceUnavailableError)

django.setup()


NAME1 = 'test_res1'
NAME2 = 'test_res2'

VERSION1 = 3
VERSION2 = 2
MODIFIED_VERSION = 5

IP_ADDRESS1 = '1.1.1.1'
IP_ADDRESS2 = '2.2.2.2'


def create_test_file(test_file_path):
    """Create a test file.

    Args:
        test_file_path (str): path of the test file to create.
    """
    open(test_file_path, 'w').close()


class BasicRotestUnitTest(TransactionTestCase):
    """Basic test for Rotest unit testing.

    Used to create a new DB for every test, and creating a Rotest test result.

    Attributes:
        RESULT_OUTPUTS (list): list of result outputs names.
    """
    RESULT_OUTPUTS = []

    def setUp(self):
        """Initialize the test's variables."""
        super(BasicRotestUnitTest, self).setUp()
        override_client_creator()
        self.result = None

    @classmethod
    def create_result(cls, main_test):
        """Create a result object for the test and starts it.

        Args:
            main_test(TestSuite / TestCase): the test to be ran.

        Returns:
            Result. a new initiated result object.
        """
        result = Result(outputs=cls.RESULT_OUTPUTS, main_test=main_test)
        result.startTestRun()
        return result

    def run_test(self, test):
        """Create a result object and run the test.

        Args:
            test (TestCase / TestSuite): test to run.
        """
        self.result = self.create_result(test)

        test.run(self.result)

    def validate_result(self, result, success, successes=0, fails=0, skips=0,
                        errors=0, expected_failures=0, unexpected_successes=0):
        """Validate that the run summary is as expected.

        Args:
            result (Result): test's result object.
            success (bool): expected 'success' state of the main test.
            successes (number): expected number of successes.
            fails (number): expected number of fails.
            skips (number): expected number of skipps.
            errors (number): expected number of errors.
            expected_failures (number): expected number of expected failures.
            unexpected_successes (number): expected number of unexpected
                successes.

        Raises:
            AssertionError: the validation failed.
        """
        self.assertEqual(len(result.failures), fails, "Unexpected number of "
                         "failures (got %d, expected %d)" %
                         (len(result.failures), fails))

        self.assertEqual(len(result.skipped), skips, "Unexpected number of "
                         "skipps (got %d, expected %d)" %
                         (len(result.skipped), skips))

        self.assertEqual(len(result.errors), errors, "Unexpected number of "
                         "errors (got %d, expected %d)" %
                         (len(result.errors), errors))

        self.assertEqual(len(result.expectedFailures), expected_failures,
                         "Unexpected number of expected failures "
                         "(got %d, expected %d)" %
                         (len(result.expectedFailures), expected_failures))

        self.assertEqual(len(result.unexpectedSuccesses), unexpected_successes,
                         "Unexpected number of unexpected successes "
                         "(got %d, expected %d)" %
                         (len(result.unexpectedSuccesses),
                          unexpected_successes))

        actual_successes = result.testsRun - sum(map(len,
                                                 (result.failures,
                                                  result.skipped,
                                                  result.errors,
                                                  result.expectedFailures,
                                                  result.unexpectedSuccesses)))

        self.assertEqual(actual_successes, successes, "Unexpected number of "
                         "successes (got %d, expected %d)" %
                         (actual_successes, successes))

        actual_success = result.main_test.data.success
        self.assertEqual(success, actual_success, "Expected success value %r "
                         "differs from actual value %r"
                        % (success, actual_success))

    def validate_resource(self, resource, dirty=True,
                          initialized=True, finalized=True):
        """Validate the state of a resource according to the paramters.

        Args:
            resource (BaseResource): resource to check.
            dirty (bool): expected dirty state.
            initialized (bool): initialized dirty state.
            finalized (bool): finalized dirty state.

        Raises:
            AssertionError. resource failed to validate.
        """
        self.assertEqual(resource.dirty, dirty,
                         "%r 'dirty' state was %r and not %r" %
                         (resource.name, resource.dirty, dirty))

        self.assertEqual(resource.initialization_flag, initialized,
                         "%r 'initialized' state was %r and not %r" %
                         (resource.name, resource.initialization_flag,
                          initialized))

        self.assertEqual(resource.finalization_flag, finalized,
                         "%r 'finalized' state was %r and not %r" %
                         (resource.name, resource.finalization_flag,
                          finalized))


class MockResourceClient(ClientResourceManager):
    """Mock resource client."""
    def __init__(self, *args, **kwargs):
        """Suppress connecting/disconnecting to/from the server."""
        super(MockResourceClient, self).__init__(*args, **kwargs)
        self.connected = False

    def is_connected(self):
        """Check if the client is connected or not.

        Returns:
            bool. True if the client is connected, False otherwise.
        """
        return self.connected

    def connect(self, *args, **kwargs):
        """Suppressed connect method."""
        self.connected = True

    def disconnect(self, *args, **kwargs):
        """Suppressed disconnect method."""
        self._release_locked_resources()
        self.connected = False

    def _lock_resources(self, descriptors, timeout=None):
        """Return resources from the DB according to the descriptors.

        Args:
            descriptors (list): list of :class:`rotest.management.common.
                resource_descriptor.ResourceDescriptor`.
            timeout (number): seconds to wait for resources if they're
                unavailable. None - use the default timeout.
                Not used in this function (it's just for the signature).

        Returns:
            list. list of locked resources.

        Raises:
            ResourceDoesNotExistError: requested resource doesn't exist.
            ResourceUnavailableError: requested resource is unavailable.
        """
        # Make sure the unittest is using the test DB, by assigning the test
        # database path as the database path to use.
        # (this is needed in multiprocess in windows)
        for db_connection in connections.databases.values():
            test_db_name = db_connection['TEST']['NAME']
            db_connection['NAME'] = test_db_name

        resources = []
        for descriptor in descriptors:
            data_type = descriptor.type.DATA_CLASS
            try:
                available_resources = data_type.objects.filter(
                                 is_usable=True, **descriptor.properties)
                if len(available_resources) == 0:
                    raise ResourceDoesNotExistError()

                resource = descriptor.type(available_resources[0])

            except ObjectDoesNotExist:  # The resource doesn't exist.
                raise ResourceDoesNotExistError()

            if resource.owner != '' or resource.reserved != '':
                raise ResourceUnavailableError()

            resources.append(resource)

        return resources

    def _release_resources(self, resources):
        """Save the current state of the resources."""
        for resource in resources:
            if resource in self.locked_resources:
                self.locked_resources.remove(resource)

        [resource.data.save() for resource in resources]

    def query_resources(self, descriptor):
        """Query the content of the server's DB.

        Args:
            descriptor (ResourceDescriptor): descriptor of the query
                (containing model class and query filter kwargs).
        """
        matches = descriptor.type.DATA_CLASS.objects.filter(is_usable=True,
                                                    **descriptor.properties)

        return [data for data in matches]


def override_client_creator():
    def create_resource_manager(self):
        """Create a new resource manager client instance.

        The resource client is overridden so it wouldn't need an actual
        resource manager in order to lock resources. This client provides
        the resources from the DB without asking any server for them.

        Returns:
            ClientResourceManager. new resource manager client.
        """
        return MockResourceClient()

    BaseTestRunner.create_resource_manager = create_resource_manager


class MockCase(TestCase):
    """Mock case for unit testing Rotest.

    This case is used by Rotest's unit tests as a mock case which doesn't
    doesn't need a real resource manager in order to get resources.
    """
    # Setting class fixture
    resources = (request('res1', DemoResource, ip_address=IP_ADDRESS1),
                 request('res2', DemoResource, ip_address=IP_ADDRESS2))

    def create_resource_manager(self):
        """Create a new resource manager client instance.

        The resource client is overridden so it wouldn't need an actual
        resource manager in order to lock resources. This client provides the
        resources from the DB without asking any server for them.

        Returns:
            ClientResourceManager. new resource manager client.
        """
        return MockResourceClient()


class FailureCase(MockCase):
    """Mock case, always fails."""
    def test_failure(self):
        """Mock test function - always fails."""
        self.fail()


class StoreFailureCase(MockCase):
    """Mock case, store failures."""
    FAILURE_MESSAGE = "Stored failure"
    ASSERTION_MESSAGE = "Assertion failed"

    def test_store_failure(self):
        """Mock test function - stores failures."""
        self.expect(False, self.FAILURE_MESSAGE)
        self.assertTrue(True, self.ASSERTION_MESSAGE)


class StoreMultipleFailuresCase(MockCase):
    """Mock case, store failures."""
    FAILURE_MESSAGE1 = "Stored failure"
    FAILURE_MESSAGE2 = "Stored failure 2"

    def test_store_failures(self):
        """Mock test function - stores failures."""
        self.expect(False, self.FAILURE_MESSAGE1)
        self.expect(False, self.FAILURE_MESSAGE2)


class StoreFailureErrorCase(MockCase):
    """Mock case, store a failure and raise exception."""
    ERROR_MESSAGE = "Error"
    FAILURE_MESSAGE = "Stored failure"

    def test_store_failure_and_error(self):
        """Mock test function - stores a failure and raise exception."""
        self.expect(False, self.FAILURE_MESSAGE)
        raise RuntimeError(self.ERROR_MESSAGE)


class ErrorCase(MockCase):
    """Mock case, raise exception."""
    def test_run(self):
        """Mock test function - raise exception."""
        raise RuntimeError()


class SuccessCase(MockCase):
    """Mock case, given the required resources always succeed."""
    def test_success(self):
        """Mock test function - always succeed."""
        pass


class DynamicResourceLockingCase(MockCase):
    """Mock case, requests a resource and validates the attributes."""
    dynamic_resources = ()

    def test_dynamic_lock(self):
        """Mock test function - always succeed."""
        self.request_resources(self.dynamic_resources)
        for resource_request in self.dynamic_resources:
            self.assertTrue(hasattr(self, resource_request.name),
                            "Failed to set attribute of resource %r" %
                            resource_request.name)
            self.assertIn(resource_request.name, self.locked_resources)


class MockRequestsCase(MockCase):
    """Mock test case, change its requests before running it."""
    def test_success(self):
        """Mock test function - always succeed."""
        pass


class ModifyResourceCase(MockCase):
    """Mock case, changes the version of its locked resource."""
    resources = (request('res', DemoResource, version=VERSION1),)

    FIELD_TO_CHANGE = NotImplemented
    VALUE_TO_SET = NotImplemented

    def test_change_version(self):
        """Alter a field of the locked resource."""
        setattr(self.res.data, self.FIELD_TO_CHANGE, self.VALUE_TO_SET)
        self.res.data.save()


class CheckResourceCase(MockCase):
    """Mock case, checks the version of its locked resource."""
    resources = (request('res', DemoResource, version=VERSION1),)

    EXPECTED_VERSION = VERSION1

    def test_version(self):
        """Verify the version of the locked resource."""
        self.assertEqual(self.res.data.version, self.EXPECTED_VERSION)


class SkipCase(MockCase):
    """Mock case, contains one test that should be skipped."""
    SKIP_MESSAGE = "Test skipped"

    def test_skip(self):
        """Mock test function - always skip."""
        raise unittest.SkipTest(self.SKIP_MESSAGE)


class ExpectedFailureCase(MockCase):
    """Mock case, given the required resources will fail as expected."""
    @unittest.case.expectedFailure
    def test_expected_failure(self):
        """Mock test function, fail as expected."""
        self.fail('expected failure')


class UnexpectedSuccessCase(MockCase):
    """Mock case, contains one test that should fail but succeeds."""
    @unittest.case.expectedFailure
    def test_unexpected_success(self):
        """Mock test function - should fail but succeeds."""
        pass


class ErrorInSetupCase(SuccessCase):
    """Mock case, raise exception after locking resources."""
    def setUp(self):
        """Mock test setup - raise exception."""
        raise RuntimeError()


class FailTwiceCase(MockCase):
    """Mock case which fails until it is run a fixed number of times.

    Attributes:
        TIMES_TO_FAIL (number): number of runs that the test fails before
            it succeeds.
        times_run (number): number of times that the test has been run.
    """
    TIMES_TO_FAIL = 2

    times_run = 0

    def test_fail_once(self):
        """Mock case - fails until it is run a fixed number of times."""
        FailTwiceCase.times_run += 1
        if FailTwiceCase.times_run <= self.TIMES_TO_FAIL:
            self.fail()


class PartialCase(FailureCase):
    """Mock case, contains one successful & one failed test method."""
    def test_success(self):
        """Success test function."""
        pass


class MockCase1(MockCase):
    """Mock test case, will contain a test."""
    def test(self):
        pass


class TwoTestsCase(MockCase):
    """Mock case, contains two test methods."""
    def test_1(self):
        "First test method."
        pass

    def test_2(self):
        "Second test method."
        pass


class MockCase2(MockCase):
    """Mock test case, will contain a test."""
    def test(self):
        pass


class MockTestSuite(TestSuite):
    """Mock test suite, will contain a sequence of tests."""
    pass


class MockSuite1(TestSuite):
    """Mock test suite, will contain a sequence of tests."""
    pass


class MockSuite2(TestSuite):
    """Mock test suite, will contain a sequence of tests."""
    pass


class MockNestedTestSuite(MockTestSuite):
    """Mock test suite, will be contained in other test cases."""
    pass


class MockTestSuite1(TestSuite):
    """Mock test suite, will contain a sequence of tests."""
    pass


class MockFlow(TestFlow):
    """Mock test flow for unit-testing blocks behavior."""
    resources = (request('res1', DemoResource, ip_address=IP_ADDRESS1),)

    def create_resource_manager(self):
        """Create a new resource manager client instance.

        The resource client is overridden so it wouldn't need an actual
        resource manager in order to lock resources. This client provides the
        resources from the DB without asking any server for them.

        Returns:
            ClientResourceManager. new resource manager client.
        """
        return MockResourceClient()


class MockFlow1(MockFlow):
    """Mock test flow for unit-testing blocks behavior."""
    resources = (request('res1', DemoResource, ip_address=IP_ADDRESS1),)


class MockFlow2(MockFlow):
    """Mock test flow for unit-testing blocks behavior."""
    resources = (request('res1', DemoResource, ip_address=IP_ADDRESS1),)


class MockSubFlow(MockFlow):
    """Mock test sub-flow for unit-testing blocks behavior."""


class MockBlock(TestBlock):
    """Mock test block for unit-testing blocks behavior."""
    pass


class NoMethodsBlock(MockBlock):
    """Mock test block that doesn't define test methods."""
    pass


class MultipleMethodsBlock(MockBlock):
    """Mock test block that defines too many test methods."""
    def test_something(self):
        """Mock test function - does nothing."""
        pass

    def test_another(self):
        """Mock test function - does nothing."""
        pass


class FailureBlock(MockBlock):
    """Mock block, always fails."""
    def test_failure(self):
        """Mock test function - always fails."""
        self.fail()


class ErrorBlock(MockBlock):
    """Mock block, raise exception."""
    def test_run(self):
        """Mock test function - raise exception."""
        raise RuntimeError()


class SuccessBlock(MockBlock):
    """Mock block, given the required resources always succeed."""
    def test_success(self):
        """Mock test function - always succeed."""
        pass


class InputsValidationBlock(SuccessBlock):
    """Mock test, change inputs definition to validate them."""
    pass


class PretendToShareDataBlock(SuccessBlock):
    """Mock test, pretend to inject data into the common object."""
    pass


class WriteToCommonBlock(MockBlock):
    """Mock test, injects data into the common object."""
    INJECT_NAME = 'some_name'
    INJECT_VALUE = 'some_value'
    outputs = (INJECT_NAME,)

    def test_inject(self):
        """Mock test function that injects data into the common object."""
        self.share_data(**{self.INJECT_NAME: self.INJECT_VALUE})


class ReadFromCommonBlock(MockBlock):
    """Mock test, reads a value and asserts it common object."""
    READ_NAME = NotImplemented
    READ_VALUE = NotImplemented

    def test_read(self):
        """Mock test function that read from the block object data."""
        self.assertEqual(getattr(self, self.READ_NAME), self.READ_VALUE)


class AttributeCheckingBlock(MockBlock):
    """Mock test, checks that the test has an attribute."""
    ATTRIBUTE_NAME = NotImplemented

    def test_attr_exists(self):
        self.assertTrue(hasattr(self, self.ATTRIBUTE_NAME))


class DynamicResourceLockingBlock(MockBlock):
    """Mock block, requests resources and validates the attributes.

    Attributes:
        is_global (bool): whether to share the resources with the other blocks.
        dynamic_resources (tuple): a list or a tuple of resources to lock.
    """
    is_global = False
    dynamic_resources = ()

    def test_dynamic_lock(self):
        """Mock test function - always succeed."""
        self.request_resources(self.dynamic_resources,
                               is_global=self.is_global)

        for resource_request in self.dynamic_resources:
            self.assertTrue(hasattr(self, resource_request.name),
                            "Failed to set attribute of resource %r" %
                            resource_request.name)

            self.assertIn(resource_request.name, self.all_resources)


class ModifyResourceBlock(MockBlock):
    """Mock block, changes the version of its locked resource."""
    resources = (request('res', DemoResource, version=VERSION1),)

    FIELD_TO_CHANGE = NotImplemented
    VALUE_TO_SET = NotImplemented

    def test_change_version(self):
        """Alter a field of the locked resource."""
        setattr(self.res.data, self.FIELD_TO_CHANGE, self.VALUE_TO_SET)
        self.res.data.save()


class CheckResourceBlock(MockBlock):
    """Mock block, checks the version of its locked resource."""
    resources = (request('res', DemoResource, version=VERSION1),)

    EXPECTED_VERSION = VERSION1

    def test_version(self):
        """Verify the version of the locked resource."""
        self.assertEqual(self.res.data.version, self.EXPECTED_VERSION)


class SkipBlock(MockBlock):
    """Mock block, contains one test that should be skipped."""
    SKIP_MESSAGE = "Test skipped"

    def test_skip(self):
        """Mock test function - always skip."""
        raise unittest.SkipTest(self.SKIP_MESSAGE)


class ExpectedFailureBlock(MockBlock):
    """Mock block, given the required resources will fail as expected."""
    @unittest.case.expectedFailure
    def test_expected_failure(self):
        """Mock test function, fail as expected."""
        self.fail('expected failure')


class UnexpectedSuccessBlock(MockBlock):
    """Mock block, contains one test that should fail but succeeds."""
    @unittest.case.expectedFailure
    def test_unexpected_success(self):
        """Mock test function - should fail but succeeds."""
        pass
