"""Test multiprocess runner timeout functionality.

This module contains tests for the multiprocess runner timeout functionality.
"""
# pylint: disable=protected-access,too-many-public-methods,invalid-name
import django

from test_runner import AbstractMultiprocessRunnerTest
from rotest.common.colored_test_runner import colored_main
from rotest.tests.core.utils import MockSuite1, MockSuite2, MockTestSuite
from utils import (BasicMultiprocessCase, TimeoutCase, SetupTimeoutCase,
                   TearDownTimeoutCase, TimeoutWithSubprocessCase)


class TestMultiprocessTimeouts(AbstractMultiprocessRunnerTest):
    """Test class for testing timeout feature in MultiprocessRunner."""

    def test_timeout_during_setup(self):
        """Test that a test case is killed if it times out during setUp.

        * Run a case which gets timeout in the setUp.
        * Validate that the case's worker is killed in time.
        * Validate the amount of PID in queue is as expected.
        """
        SetupTimeoutCase.pid_queue = self.pid_queue
        SetupTimeoutCase.post_timeout_event = self.post_timeout_event

        MockTestSuite.components = (SetupTimeoutCase,)

        self.runner.run(MockTestSuite)

        self.assertFalse(self.post_timeout_event.is_set(),
                         "Process continued when it should have been "
                         "terminated due to timeout")

        self.validate_test_processes(1)

    def test_timeout_during_test_method(self):
        """Test that a test case is killed if a timeout elapses.

        * Run a case which gets timeout.
        * Validate that the case's worker is killed in time.
        * Validate the amount of PID in queue is as expected.
        """
        TimeoutCase.pid_queue = self.pid_queue
        TimeoutCase.post_timeout_event = self.post_timeout_event

        MockTestSuite.components = (TimeoutCase,)

        self.runner.run(MockTestSuite)

        self.assertFalse(self.post_timeout_event.is_set(),
                         "Process continued when it should have been "
                         "terminated due to timeout")

        self.validate_test_processes(1)

    def test_timeout_during_teardown(self):
        """Test that a test whose tearDown got timeout also gets killed.

        * Create a case which gets timeout in its tearDown.
        * Validate that the case's worker is killed in time.
        * Validate the amount of PID in queue is as expected.
        """
        TearDownTimeoutCase.pid_queue = self.pid_queue
        TearDownTimeoutCase.post_timeout_event = self.post_timeout_event

        MockTestSuite.components = (TearDownTimeoutCase,)

        self.runner.run(MockTestSuite)

        self.assertFalse(self.post_timeout_event.is_set(),
                         "Process continued when it should have been "
                         "terminated due to timeout")

        self.validate_test_processes(1)

    def test_suite_continues_after_timeout(self):
        """Test that a test suite continues to run after a case is killed.

        * Create a suite composed of a case which gets timeout and a case which
              run successfully.
        * Validate that the first case was killed in time.
        * Validate that the second case was run.
        """
        TimeoutCase.pid_queue = self.pid_queue
        TimeoutCase.post_timeout_event = self.post_timeout_event

        BasicMultiprocessCase.pid_queue = self.pid_queue
        BasicMultiprocessCase.post_timeout_event = self.post_timeout_event

        MockSuite1.components = (TimeoutCase,)
        MockSuite2.components = (BasicMultiprocessCase,)

        MockTestSuite.components = (MockSuite1, MockSuite2)

        self.runner.run(MockTestSuite)

        self.assertFalse(self.post_timeout_event.is_set(),
                         "Process continued when it should have been "
                         "terminated due to timeout")

        self.validate_test_processes(2)

    def test_suite_continues_after_teardown_timeout(self):
        """Test that tests continue to run after a case is killed in tearDown.

        * Create a suite composed of a case which gets timeout during tearDown
            and a case which run successfully.
        * Validate that the first case was killed in time.
        * Validate that the second case was run.
        """
        TearDownTimeoutCase.pid_queue = self.pid_queue
        TearDownTimeoutCase.post_timeout_event = self.post_timeout_event

        BasicMultiprocessCase.pid_queue = self.pid_queue
        BasicMultiprocessCase.post_timeout_event = self.post_timeout_event

        MockSuite1.components = (TearDownTimeoutCase,)
        MockSuite2.components = (BasicMultiprocessCase,)

        MockTestSuite.components = (MockSuite1, MockSuite2)

        self.runner.run(MockTestSuite)

        self.assertFalse(self.post_timeout_event.is_set(),
                         "Process continued when it should have been "
                         "terminated due to timeout")

        self.validate_test_processes(2)

    def test_subprocess_killed_timeout(self):
        """Test that subprocess get killed when case get killed.

        * Runs a test which opens a subprocess, and sleeps until timeout.
        * Validates that two processes were run (worker and subprocess).
        * Validates that both process got killed.
        """
        TimeoutWithSubprocessCase.pid_queue = self.pid_queue
        TimeoutWithSubprocessCase.post_timeout_event = self.post_timeout_event

        MockTestSuite.components = (TimeoutWithSubprocessCase,)

        self.runner.run(MockTestSuite)

        self.assertFalse(self.post_timeout_event.is_set(),
                         "Process continued when it should have been "
                         "terminated due to timeout")

        self.validate_test_processes(2)


if __name__ == '__main__':
    django.setup()
    colored_main(defaultTest='TestMultiprocessTimeouts', verbosity=2)
