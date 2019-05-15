"""Test multiprocess runner functionality.

This module contains tests for the runners' results.
"""
# pylint: disable=too-many-arguments
# pylint: disable=relative-import,invalid-name,too-many-public-methods
from __future__ import absolute_import

import sys
import unittest
from abc import ABCMeta
from multiprocessing import Queue, Event

from six import StringIO
from future import standard_library
from future.utils import with_metaclass

from rotest.core.runner import BaseTestRunner
from rotest.core.models.general_data import GeneralData
from rotest.core.runners.multiprocess.manager.runner import MultiprocessRunner

from tests.core.multiprocess.utils import (TimeoutCase, SuicideCase,
                                           SetupTimeoutFlow, SetupCrashFlow)
from tests.core.utils import (FailureCase, SuccessCase, ErrorCase, SkipCase,
                              UnexpectedSuccessCase, ExpectedFailureCase,
                              SuccessMessageCase, MockSuite1, MockSuite2,
                              MockTestSuite, StoreMultipleFailuresCase,
                              StoreFailureErrorCase, TwoTestsCase,
                              BasicRotestUnitTest)

standard_library.install_aliases()


class AbstractTestRunnerResult(with_metaclass(ABCMeta, BasicRotestUnitTest)):
    """Abstract test class for testing the runners' behavior."""
    __test__ = False

    fixtures = ['case_ut.json']

    def get_runner(self):
        """Create and return the relevant test runner.

        Returns:
            BaseTestRunner. test runner object.
        """
        raise NotImplementedError()

    def setUp(self):
        """Initialize the test runner."""
        super(AbstractTestRunnerResult, self).setUp()

        self.runner = self.get_runner()

        sys.stdout = StringIO()  # Suppress the runner's prints.

    def validate_all_finished(self, test):
        """Validate the state of the test and its sub-tests is finished.

        Args:
            result (TestSuite / TestCase): test object.

        Raises:
            AssertionError: not all the tests are finished.
        """
        self.assertEqual(test.data.status, GeneralData.FINISHED,
                         "%r was run fully but its status in the DB isn't "
                         "finished. Current status: %r" %
                         (test.data.name, test.data.status))

        if isinstance(test, unittest.TestSuite):
            for sub_test in test:
                self.validate_all_finished(sub_test)

    def test_success(self):
        """Validate the result of a simple case of success."""
        MockSuite1.components = (SuccessCase, SuccessCase)
        MockSuite2.components = (SuccessCase,)
        MockTestSuite.components = (MockSuite1, MockSuite2)

        self.runner.run(MockTestSuite)
        test = self.runner.test_item
        result = self.runner.result

        self.validate_all_finished(test)
        self.validate_result(result, True, successes=3)

    def test_info(self):
        """Validate behavior of success messages."""
        MockTestSuite.components = (SuccessMessageCase,)

        self.runner.run(MockTestSuite)
        test = self.runner.test_item
        result = self.runner.result

        self.validate_all_finished(test)
        self.validate_result(result, True, successes=1)
        self.assertEqual(list(test)[0].data.traceback,
                         SuccessMessageCase.MESSAGE,
                         "Success message wasn't registered")

    def test_standalone_case(self):
        """Validate that a TestCase can run on its own."""
        self.runner.run(TwoTestsCase)
        test = self.runner.test_item
        result = self.runner.result

        self.validate_all_finished(test)
        self.validate_result(result, True, successes=2)

    def test_fail(self):
        """Validate the result of a simple case of failure."""
        MockSuite1.components = (SuccessCase, FailureCase)
        MockSuite2.components = (SuccessCase,)
        MockTestSuite.components = (MockSuite1, MockSuite2)

        self.runner.run(MockTestSuite)
        test = self.runner.test_item
        result = self.runner.result

        self.validate_all_finished(test)
        self.validate_result(result, False, successes=2, fails=1)

    def test_stored_failures(self):
        """Validate the result of a simple case of stored failure."""
        MockSuite1.components = (SuccessCase, StoreFailureErrorCase)
        MockSuite2.components = (StoreMultipleFailuresCase,)
        MockTestSuite.components = (MockSuite1, MockSuite2)

        self.runner.run(MockTestSuite)
        test = self.runner.test_item
        result = self.runner.result

        self.validate_all_finished(test)
        # Since number of tests (3) minus errors and failures is -1,
        # expect that number of 'successes'
        self.validate_result(result, False, successes=-1, fails=3, errors=1)

    def test_error(self):
        """Validate the result of a simple case of error."""
        MockSuite1.components = (SuccessCase, ErrorCase)
        MockSuite2.components = (SuccessCase,)
        MockTestSuite.components = (MockSuite1, MockSuite2)

        self.runner.run(MockTestSuite)
        test = self.runner.test_item
        result = self.runner.result

        self.validate_all_finished(test)
        self.validate_result(result, False, successes=2, errors=1)

    def test_success_and_skip(self):
        """Validate the result of success and skip."""
        MockSuite1.components = (SuccessCase, SkipCase)
        MockSuite2.components = (SuccessCase,)
        MockTestSuite.components = (MockSuite1, MockSuite2)

        self.runner.run(MockTestSuite)
        test = self.runner.test_item
        result = self.runner.result

        self.validate_all_finished(test)
        self.validate_result(result, True, successes=2, skips=1)

    def test_only_skip(self):
        """Validate the result of a simple case of skip."""
        MockSuite1.components = (SkipCase,)
        MockTestSuite.components = (MockSuite1,)

        self.runner.run(MockTestSuite)
        test = self.runner.test_item
        result = self.runner.result

        self.validate_all_finished(test)
        self.validate_result(result, None, skips=1)

    def test_unexpected_success(self):
        """Validate the result of a simple case of unexpected success."""
        MockSuite1.components = (SuccessCase, UnexpectedSuccessCase)
        MockSuite2.components = (SuccessCase,)
        MockTestSuite.components = (MockSuite1, MockSuite2)

        self.runner.run(MockTestSuite)
        test = self.runner.test_item
        result = self.runner.result

        self.validate_all_finished(test)
        self.validate_result(result, False, successes=2,
                             unexpected_successes=1)

    def test_expected_failure(self):
        """Validate the result of a simple case of expected failure."""
        MockSuite1.components = (SuccessCase, ExpectedFailureCase)
        MockSuite2.components = (SuccessCase,)
        MockTestSuite.components = (MockSuite1, MockSuite2)

        self.runner.run(MockTestSuite)
        test = self.runner.test_item
        result = self.runner.result

        self.validate_all_finished(test)
        self.validate_result(result, True, successes=2, expected_failures=1)

    def test_linked_false(self):
        """Validate that the tests under a TestSuite are not linked."""
        MockSuite1.components = (FailureCase, SuccessCase)
        MockSuite2.components = (SuccessCase,)
        MockTestSuite.components = (MockSuite1, MockSuite2)

        self.runner.run(MockTestSuite)
        test = self.runner.test_item
        result = self.runner.result

        self.validate_all_finished(test)
        self.validate_result(result, False, successes=2, fails=1)


class TestMultiprocessRunnerResult(AbstractTestRunnerResult):
    """Test class for testing the multiprocess runner's behavior.

    Attributes:
        NUMBER_OF_PROCESSES (number): number of worker processes the
            MultiprocessRunner should use.
    """
    __test__ = True

    NUMBER_OF_PROCESSES = 1

    def get_runner(self):
        """Create and return the relevant test runner.

        Returns:
            MultiprocessRunner. test runner object.
        """
        return MultiprocessRunner(outputs=[],
                                  config=None,
                                  run_name=None,
                                  run_delta=False,
                                  save_state=False,
                                  enable_debug=False,
                                  workers_number=self.NUMBER_OF_PROCESSES)

    def test_timeout_result(self):
        """Validate runner result in case of a timeout."""
        TimeoutCase.pid_queue = Queue()
        TimeoutCase.post_timeout_event = Event()

        MockSuite1.components = (TimeoutCase,)
        MockSuite2.components = (SuccessCase, SuccessCase)
        MockTestSuite.components = (MockSuite1, MockSuite2)

        self.runner.run(MockTestSuite)
        self.validate_all_finished(self.runner.test_item)
        self.validate_result(self.runner.result, False, successes=2, errors=1)

    def test_flow_timeout(self):
        """Validate runner result in case of a timeout in flow's setUp."""
        TimeoutCase.pid_queue = Queue()
        TimeoutCase.post_timeout_event = Event()

        MockTestSuite.components = (SetupTimeoutFlow, SuccessCase)

        self.runner.run(MockTestSuite)
        self.validate_all_finished(self.runner.test_item)
        self.validate_result(self.runner.result, False, successes=1, errors=1)

    def test_worker_crash_result(self):
        """Validate runner result in case of worker process crash."""
        MockSuite1.components = (SuicideCase,)
        MockSuite2.components = (SuccessCase, SuccessCase)
        MockTestSuite.components = (MockSuite1, MockSuite2)

        self.runner.run(MockTestSuite)
        self.validate_all_finished(self.runner.test_item)
        self.validate_result(self.runner.result, False, successes=2, errors=1)

    def test_flow_crash_result(self):
        """Validate runner result in case of flow process crash."""
        MockSuite1.components = (SetupCrashFlow, SuccessCase)
        MockSuite2.components = (SuccessCase,)
        MockTestSuite.components = (MockSuite1, MockSuite2)

        self.runner.run(MockTestSuite)
        self.validate_all_finished(self.runner.test_item)
        self.validate_result(self.runner.result, False, successes=2, errors=1)

    def test_mid_test_timeout_result(self):
        """Validate runner result in case of a mid-test timeout."""
        TimeoutCase.pid_queue = Queue()
        TimeoutCase.post_timeout_event = Event()

        MockSuite1.components = (TimeoutCase, SuccessCase)
        MockSuite2.components = (SuccessCase,)
        MockTestSuite.components = (MockSuite1, MockSuite2)

        self.runner.run(MockTestSuite)
        self.validate_result(self.runner.result, False, successes=2, errors=1)

    def test_mid_test_crash_result(self):
        """Validate runner result of a mid-test of crash."""
        MockSuite1.components = (SuicideCase, SuccessCase)
        MockSuite2.components = (SuccessCase,)
        MockTestSuite.components = (MockSuite1, MockSuite2)

        self.runner.run(MockTestSuite)
        self.validate_result(self.runner.result, False, successes=2, errors=1)


class TestBaseRunnerResult(AbstractTestRunnerResult):
    """Test class for testing the base runner's behavior."""
    __test__ = True

    def get_runner(self):
        """Create and return the relevant test runner.

        Returns:
            BaseTestRunner. test runner object.
        """
        client = BaseTestRunner(outputs=[],
                                config=None,
                                run_name=None,
                                run_delta=False,
                                save_state=False,
                                enable_debug=False,
                                stream=StringIO())
        return client
