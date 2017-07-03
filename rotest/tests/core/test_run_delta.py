"""Test run delta feature."""
# pylint: disable=protected-access,too-many-public-methods,invalid-name
import django

from rotest.core.runner import run
from rotest.core.models.run_data import RunData
from rotest.core.models.case_data import TestOutcome
from rotest.tests.core.utils import BasicRotestUnitTest
from rotest.common.colored_test_runner import colored_main
from rotest.core.result.handlers.db_handler import DBHandler
from utils import (ErrorCase, SuccessCase, FailureCase, SkipCase,
                   MockSuite1, MockSuite2, MockNestedTestSuite,
                   MockTestSuite, FailTwiceCase, MockFlow, MockFlow1,
                   MockFlow2, SuccessBlock, FailureBlock, SkipBlock)


class TestRunDelta(BasicRotestUnitTest):
    """Test run delta behavior on successful, failed & skipped components."""
    DELTA_ITERATIONS = 3

    fixtures = ['case_ut.json']

    RESULT_OUTPUTS = [DBHandler.NAME]

    def setUp(self):
        """Create a run data the enabled running in delta mode."""
        super(TestRunDelta, self).setUp()
        self.run_data = RunData(run_delta=True)

    def test_successful_case(self):
        """Test run delta with two success cases.

        * Runs a suite with success cases.
        * Validates all tests were ran.
        * Runs the same cases with delta flag.
        * Validates no test was run.
        """
        MockSuite1.components = (SuccessCase,)
        MockSuite2.components = (SuccessCase,)

        MockTestSuite.components = (MockSuite1, MockSuite2)

        main_test = MockTestSuite()
        result = self.create_result(main_test)
        main_test.run(result)

        self.validate_result(result, True, successes=2)

        main_test = MockTestSuite(run_data=self.run_data)
        delta_result = self.create_result(main_test)
        main_test.run(delta_result)

        self.validate_result(delta_result, None, skips=2)

    def test_failure_case(self):
        """Test run delta with failure case.

        * Runs a suite with success & failure cases.
        * Validates two tests ran.
        * Runs the same cases with delta flag.
        * Validates that all the tests which weren't successful in previous
          run, ran in the second run.
        """
        MockSuite1.components = (SuccessCase,)
        MockSuite2.components = (FailureCase,)

        MockTestSuite.components = (MockSuite1, MockSuite2)

        main_test = MockTestSuite()
        result = self.create_result(main_test)
        main_test.run(result)

        self.validate_result(result, False, successes=1, fails=1)

        main_test = MockTestSuite(run_data=self.run_data)
        delta_result = self.create_result(main_test)
        main_test.run(delta_result)

        self.validate_result(delta_result, False, skips=1, fails=1)

    def test_error_case(self):
        """Test run delta with error case.

        * Runs a suite with success & error cases.
        * Validates all tests were ran.
        * Runs the same cases with delta flag.
        * Validates that all the tests which weren't successful in previous
          run, ran in the second run.
        """
        MockSuite1.components = (SuccessCase,)
        MockSuite2.components = (ErrorCase,)

        MockTestSuite.components = (MockSuite1, MockSuite2)

        main_test = MockTestSuite()
        result = self.create_result(main_test)
        main_test.run(result)

        self.validate_result(result, False, successes=1, errors=1)

        main_test = MockTestSuite(run_data=self.run_data)
        delta_result = self.create_result(main_test)
        main_test.run(delta_result)

        self.validate_result(delta_result, False, skips=1, errors=1)

    def test_skipped_case(self):
        """Test run delta with skip case.

        * Runs a suite with success & skip cases.
        * Validates all tests were ran.
        * Runs the same cases with delta flag.
        * Validates that all the tests which weren't successful in previous
          run, ran in the second run.
        """
        MockSuite1.components = (SuccessCase,)
        MockSuite2.components = (SkipCase,)

        MockTestSuite.components = (MockSuite1, MockSuite2)

        main_test = MockTestSuite()
        result = self.create_result(main_test)
        main_test.run(result)

        self.validate_result(result, True, successes=1, skips=1)

        main_test = MockTestSuite(run_data=self.run_data)
        delta_result = self.create_result(main_test)
        main_test.run(delta_result)

        self.validate_result(delta_result, None, skips=2)

    def test_different_result_cases(self):
        """Test run delta with success, failure & skip cases.

        * Runs a suite with success failure & skipped cases.
        * Validates all the tests were ran.
        * Runs the same cases with delta flag.
        * Validates that all the tests which weren't successful in previous
          run, ran in the second run.
        """
        MockSuite1.components = (SuccessCase, FailureCase)
        MockSuite2.components = (FailureCase, SkipCase)

        MockTestSuite.components = (MockSuite1, MockSuite2)

        main_test = MockTestSuite()
        result = self.create_result(main_test)
        main_test.run(result)

        self.validate_result(result, False, successes=1, skips=1, fails=2)

        main_test = MockTestSuite(run_data=self.run_data)
        delta_result = self.create_result(main_test)
        main_test.run(delta_result)

        self.validate_result(delta_result, False, skips=2, fails=2)

    def test_nested_suite(self):
        """Test run delta with nested suite.

        * Runs a nested suite.
        * Validates all the tests were ran.
        * Runs the same suite with delta flag.
        * Validates that all the tests which weren't successful in previous
          run, ran in the second run.
        """
        MockSuite1.components = (SuccessCase, FailureCase)
        MockSuite2.components = (ErrorCase, SkipCase)

        MockNestedTestSuite.components = (MockSuite1, MockSuite2)

        MockTestSuite.components = (MockSuite1, MockNestedTestSuite)

        main_test = MockTestSuite()
        result = self.create_result(main_test)
        main_test.run(result)

        self.validate_result(result, False, successes=2, skips=1, fails=2,
                             errors=1)

        main_test = MockTestSuite(run_data=self.run_data)
        delta_result = self.create_result(main_test)
        main_test.run(delta_result)

        self.validate_result(delta_result, False, skips=3, fails=2, errors=1)

    def test_cases_in_suite(self):
        """Test run delta with success, failure & skip cases.

        * Runs a suite with success failure & skipped cases.
        * Validates all the tests were run.
        * Runs the same suite with delta flag.
        * Validates that all the tests which weren't successful in previous
          run, ran in the second run.
        """
        MockTestSuite.components = (SuccessCase, FailureCase,
                                    ErrorCase, SkipCase)

        main_test = MockTestSuite()
        result = self.create_result(main_test)
        main_test.run(result)

        self.validate_result(result, False, successes=1, skips=1, fails=1,
                             errors=1)

        main_test = MockTestSuite(run_data=self.run_data)
        delta_result = self.create_result(main_test)
        main_test.run(delta_result)

        self.validate_result(delta_result, False, skips=2, fails=1, errors=1)

    def test_flow_success(self):
        """Test run delta with successful flow.

        * Runs a flow with success blocks.
        * Validates all the tests were run.
        * Runs the same suite with delta flag.
        * Validates that the flow didn't run again.
        * Runs the same suite with delta flag.
        * Validates that the flow didn't run again.
        """
        MockFlow.blocks = (SuccessBlock, SkipBlock, SuccessBlock)

        main_test = MockFlow()
        result = self.create_result(main_test)
        main_test.run(result)

        self.validate_result(result, True, successes=1)

        main_test = MockFlow(run_data=self.run_data)
        delta_result = self.create_result(main_test)
        main_test.run(delta_result)

        self.validate_result(delta_result, None, skips=1)

        main_test = MockFlow(run_data=self.run_data)
        delta_result = self.create_result(main_test)
        main_test.run(delta_result)

        self.validate_result(delta_result, None, skips=1)

    def test_failing_flow(self):
        """Test run delta with failing flow.

        * Runs a flow with success failure & skipped blocks.
        * Validates all the block were run.
        * Runs the same flow with delta flag.
        * Validates that all the blocks ran again.
        """
        MockFlow.blocks = (SuccessBlock, SkipBlock, FailureBlock)

        main_test = MockFlow()
        result = self.create_result(main_test)
        main_test.run(result)

        self.validate_result(result, False, fails=1)
        block_results1 = [block.data.exception_type for block in main_test]

        main_test = MockFlow(run_data=self.run_data)
        delta_result = self.create_result(main_test)
        main_test.run(delta_result)

        self.validate_result(delta_result, False, fails=1)
        block_results2 = [block.data.exception_type for block in main_test]
        self.assertEqual(block_results1, block_results2)

    def test_flows_in_suite(self):
        """Test run delta with success & failure flows.

        * Runs a suite with success & failure flows.
        * Validates all the tests were run.
        * Runs the same suite with delta flag.
        * Validates that all the flows which weren't successful in previous
          run, ran in the second run.
        """
        MockFlow1.blocks = (SuccessBlock, FailureBlock)
        MockFlow2.blocks = (SuccessBlock, SuccessBlock)
        MockTestSuite.components = (MockFlow2, MockFlow1, MockFlow2)

        main_test = MockTestSuite()
        result = self.create_result(main_test)
        main_test.run(result)

        self.validate_result(result, False, successes=2, fails=1)

        main_test = MockTestSuite(run_data=self.run_data)
        delta_result = self.create_result(main_test)
        main_test.run(delta_result)

        self.validate_result(delta_result, False, skips=2, fails=1)

    def test_blocks_in_different_flows(self):
        """Test run delta with success, failure & skip cases.

        * Runs a suite with success failure & skipped cases.
        * Validates all the tests were run.
        * Runs the same suite with delta flag.
        * Validates that all the tests which weren't successful in previous
          run, ran in the second run.
        """
        MockFlow1.blocks = (SuccessBlock, SuccessBlock)
        MockFlow2.blocks = (SuccessBlock, SuccessBlock)
        MockTestSuite.components = (MockFlow1, MockFlow2)

        main_test = MockTestSuite(run_data=self.run_data)
        delta_result = self.create_result(main_test)
        main_test.run(delta_result)

        self.validate_result(delta_result, True, successes=2)

    def validate_suite_data(self, suite_data, was_successful, successes=0,
                           skips=0, fails=0):
        """Validate a suite's result by its data.

        Args:
            suite_data (rotest.core.suite_data.SuiteData): data of the run
                suite to validate.
            was_successful (bool): expected 'success' status of the run suite.
            tests_run (number): expected amount of tests in current running.
            successes (number): expected amount of successful tests in current
                running.

        Raises:
            AssertionError: expected test results are not the actual results.
        """
        self.assertEqual(suite_data.success, was_successful, "The 'success' "
                         "value was wrong, expected %d, but %d ran"
                         % (was_successful, suite_data.success))

        sub_components = suite_data.get_sub_tests_data()

        actual_successful = len([case for case in sub_components
                             if case.exception_type is TestOutcome.SUCCESS])
        self.assertEqual(actual_successful, successes,
                         "The number of successful cases was wrong, expected "
                         "%d, got: %d" % (successes, actual_successful))

        actual_skips = len([case for case in sub_components
                            if case.exception_type is TestOutcome.SKIPPED])
        self.assertEqual(actual_skips, skips,
                         "The number of skipped cases was wrong, expected "
                         "%d, got: %d" % (skips, actual_skips))

        actual_fails = len([case for case in sub_components
                            if case.exception_type is TestOutcome.FAILED])
        self.assertEqual(actual_fails, fails,
                         "The number of failed cases was wrong, expected "
                         "%d, got: %d" % (fails, actual_fails))

    def test_delta_iterations(self):
        """Test run delta with iterations.

        * Runs a suite with success & success-after-three-runs cases.
        * Validates that in the first run, both tests were run and one
          succeeded.
        * Validates that in the second run, one test was run, and didn't
          succeed.
        * Validates that in the third run, one test was run successfully.
        """
        MockTestSuite.components = (SuccessCase, FailTwiceCase)

        runs_data = run(MockTestSuite, delta_iterations=self.DELTA_ITERATIONS,
                        outputs=(DBHandler.NAME,))
        run_suites = [run_data.main_test for run_data in runs_data]
        full_suite, first_delta_suite, second_delta_suite = run_suites

        self.validate_suite_data(full_suite, False, successes=1, fails=1)
        self.validate_suite_data(first_delta_suite, False, skips=1, fails=1)
        self.validate_suite_data(second_delta_suite, True, successes=1,
                                 skips=1)

    def test_different_run_names(self):
        """Test run delta on runs with different run names.

        * Runs a suite with success & failure cases with name X.
        * Validates that both tests were run and one succeeded.
        * Runs a suite with success & failure cases with name Y.
        * Validates that both tests were run and one succeeded.
        * Runs a suite with success & failure cases with name X.
        * Validates that only one test was run (the failing test of the
          previous X run) and it failed again.
        """
        MockTestSuite.components = (SuccessCase, FailureCase)

        run_data, = run(MockTestSuite, delta_iterations=1,
                        outputs=(DBHandler.NAME,), run_name='run1')
        self.validate_suite_data(run_data.main_test, False, successes=1,
                                 fails=1)

        run_data, = run(MockTestSuite, delta_iterations=1,
                        outputs=(DBHandler.NAME,), run_name='run2')
        self.validate_suite_data(run_data.main_test, False, successes=1,
                                 fails=1)

        run_data, = run(MockTestSuite, delta_iterations=1,
                        outputs=(DBHandler.NAME,), run_name='run1')
        self.validate_suite_data(run_data.main_test, False, skips=1, fails=1)

    def test_no_run_name_doesnt_filter(self):
        """Test that giving no run name doesn't filter the results.

        * Runs a suite with success & failure cases with name X.
        * Validates that both tests were run and one succeeded.
        * Runs a suite with success & failure cases with no name.
        * Validates that only one test was run (the failing test of the
          previous X run) and it failed again.
        """
        MockTestSuite.components = (SuccessCase, FailureCase)

        run_data, = run(MockTestSuite, delta_iterations=1,
                        outputs=(DBHandler.NAME,), run_name='run1')
        self.validate_suite_data(run_data.main_test, False, successes=1,
                                 fails=1)

        run_data, = run(MockTestSuite, delta_iterations=1,
                        outputs=(DBHandler.NAME,), run_name=None)
        self.validate_suite_data(run_data.main_test, False, skips=1, fails=1)

    def test_no_run_name_is_filtered(self):
        """Test that a run with no run name is filtered when running with name.

        * Runs a suite with success & failure cases with no name.
        * Validates that both tests were run and one succeeded.
        * Runs a suite with success & failure cases with name X.
        * Validates that both tests were run and one succeeded.
        """
        MockTestSuite.components = (SuccessCase, FailureCase)

        run_data, = run(MockTestSuite, delta_iterations=1,
                        outputs=(DBHandler.NAME,), run_name=None)
        self.validate_suite_data(run_data.main_test, False, successes=1,
                                 fails=1)

        run_data, = run(MockTestSuite, delta_iterations=1,
                        outputs=(DBHandler.NAME,), run_name='run1')
        self.validate_suite_data(run_data.main_test, False, successes=1,
                                 fails=1)


if __name__ == '__main__':
    django.setup()
    colored_main(defaultTest='TestRunDelta')
