"""Abstract class for all result handler tests."""
from itertools import izip
from abc import ABCMeta, abstractmethod

from django.test.testcases import TransactionTestCase

from rotest.core.suite import TestSuite
from rotest.core.models.case_data import TestOutcome, CaseData
from rotest.management.common.utils import \
                                    set_resource_manager_hostname, LOCALHOST
from rotest.tests.core.utils import (MockCase1, MockCase2, MockTestSuite,
                                     MockSuite2, MockSuite1, FailureBlock,
                                     MockNestedTestSuite, MockFlow2,
                                     SkipBlock, SuccessBlock, MockFlow1)


def get_tests(test):
    """Yield all the leaves of the test tree.

    Args:
        test (TestSuite / TestCase): a test item.

    Yields:
        rotest.core.case.TestCase. the next case that's included in the
            given test hierarchy.
    """
    if isinstance(test, TestSuite) is False:
        yield test

    if test.IS_COMPLEX is True:
        for sub_test in test:
            for leaf in get_tests(sub_test):
                yield leaf


class BaseResultHandlerTest(TransactionTestCase):
    """Base class for testing result handlers."""
    __metaclass__ = ABCMeta

    fixtures = ['resource_ut.json']

    RESULT_MESSAGES = {TestOutcome.SUCCESS: [],
                       TestOutcome.FAILED: ['Fail'],
                       TestOutcome.ERROR: ['Error'],
                       TestOutcome.SKIPPED: ['Skip'],
                       TestOutcome.UNEXPECTED_SUCCESS: [],
                       TestOutcome.EXPECTED_FAILURE: ['Expected failure']}

    EXPECTED_RESULTS = (TestOutcome.SUCCESS,
                        TestOutcome.SUCCESS,
                        TestOutcome.SKIPPED,
                        TestOutcome.FAILED,
                        TestOutcome.SUCCESS,
                        TestOutcome.FAILED,
                        TestOutcome.SUCCESS,
                        TestOutcome.ERROR,
                        TestOutcome.FAILED,
                        TestOutcome.SKIPPED,
                        TestOutcome.EXPECTED_FAILURE,
                        TestOutcome.UNEXPECTED_SUCCESS)

    @classmethod
    def setUpClass(cls):
        """Set the server host to be the localhost.

        This will allow the resource manager server and the
        tests to use the same DB.
        """
        super(BaseResultHandlerTest, cls).setUpClass()

        set_resource_manager_hostname(LOCALHOST)

    @abstractmethod
    def get_result_handler(self):
        """Return an instance of the tested handler."""
        pass

    def setUp(self):
        """Create a test tree for the test.

        The hierarchy of the tests is:

        * MockNestedTestSuite
            * MockTestSuite
                * MockFlow1
                    * SuccessBlock
                    * SkipBlock
                * MockSuite1
                    * MockFlow2
                        * SuccessBlock
                        * FailureBlock
                    * MockCase1
                    * MockCase1
                    * MockCase2
            * MockSuite2
                * MockCase2
                * MockCase2
                * MockCase1
        """
        MockFlow1.blocks = (SuccessBlock, SkipBlock)
        MockFlow2.blocks = (SuccessBlock, FailureBlock)
        MockSuite1.components = (MockFlow2, MockCase2, MockCase1, MockCase2)
        MockSuite2.components = (MockCase2, MockCase2, MockCase1)
        MockTestSuite.components = (MockFlow1, MockSuite1)
        MockNestedTestSuite.components = (MockTestSuite, MockSuite2)
        self.main_test = MockNestedTestSuite()
        self.components = get_tests(self.main_test)
        self.handler = self.get_result_handler()

    def validate_start_test_run(self):
        """Validate the output of the handler's start_test_run method."""
        pass

    def validate_result(self, test, result, traceback=""):
        """Validate adding result gives the expected output.

        Args:
            test (rotest.core.case.TestCase): the test its result was added.
            result (str): result to add to the test.
            traceback (str): the traceback of the test.

        Raises:
            AsserationError. the result wasn't added as expected.
        """
        pass

    def validate_stop_test_run(self):
        """Validate the handler's stop_test_run output is as expected."""
        pass

    def test_handler(self):
        """Test the starting and ending of a test, and adding test results."""
        self.handler.start_test_run()
        self.validate_start_test_run()

        result_to_method = {
          TestOutcome.ERROR: self.handler.add_error,
          TestOutcome.SKIPPED: self.handler.add_skip,
          TestOutcome.FAILED: self.handler.add_failure,
          TestOutcome.SUCCESS: self.handler.add_success,
          TestOutcome.EXPECTED_FAILURE: self.handler.add_expected_failure,
          TestOutcome.UNEXPECTED_SUCCESS: self.handler.add_unexpected_success}

        for case, result_index in izip(self.components,
                                                 self.EXPECTED_RESULTS):

            result = CaseData.RESULT_CHOICES[result_index]
            self.handler.start_test(case)
            case.data.exception_type = result_index
            result_method = result_to_method[result_index]
            result_args = self.RESULT_MESSAGES[result_index]
            if len(result_args) > 0:
                case.data.traceback = result_args[0]

            result_method(case, *result_args)
            self.handler.update_resources(case)

            self.validate_result(case, result, *result_args)

        self.handler.stop_test_run()
        self.validate_stop_test_run()
