"""Test multiprocess runner.

This module contains tests for the multiprocess runner functionality.
"""
# pylint: disable=protected-access,too-many-public-methods,invalid-name
import os
import psutil
import unittest
from Queue import Empty
from multiprocessing import Queue, Event

import django

from rotest.common.colored_test_runner import colored_main
from rotest.tests.core.utils import MockSuite1, BasicRotestUnitTest
from rotest.core.runners.multiprocess.manager.runner import MultiprocessRunner
from utils import (BasicMultiprocessCase, SubprocessCreationCase,
                   ResourceIdRegistrationCase, RegisterInSetupFlow)


class AbstractMultiprocessRunnerTest(BasicRotestUnitTest):
    """Abstract test for Multiprocess Runner.

    Attributes:
        PROCESSES_NUMBER (number): number of worker processes the
            MultiprocessRunner should use.
        post_timeout_event (Multiprocessing.Event): will be 'set' only if case
            exceeded timeout limits.
        pid_queue (Multiprocessing.Queue): A queue to store different PIDs
            related to the case.
    """
    PROCESSES_NUMBER = 1

    fixtures = ['case_ut.json']

    def setUp(self):
        """Initialize the test runner and create cases' variables."""
        super(AbstractMultiprocessRunnerTest, self).setUp()

        self.pid_queue = Queue()
        self.post_timeout_event = Event()

        self.runner = MultiprocessRunner(outputs=[],
                                         config=None,
                                         run_name=None,
                                         run_delta=False,
                                         save_state=False,
                                         enable_debug=False,
                                         workers_number=self.PROCESSES_NUMBER)

    def validate_test_processes(self, expected_processes_num):
        """Validate that case's processes ran and were killed.

         * Validate that expected number of processes ran.
         * Validate that all processes got killed.

        Args:
            expected_processes (number): expected number of processes to
                validate.

        Raises:
            AssertionError. of one or more of the processes wasn't killed.
        """
        for _ in xrange(expected_processes_num):
            pid = self.pid_queue.get_nowait()
            self.assertFalse(psutil.pid_exists(pid),
                            "Process %s wasn't killed" % pid)

    def get_pids(self):
        """Return all available IDs in the queue.

        Yields:
            number. IDs in the queue.
        """
        try:
            while True:
                yield self.pid_queue.get_nowait()

        except Empty:
            pass


class TestMultiprocessRunner(AbstractMultiprocessRunnerTest):
    """Test class for testing MultiprocessRunner."""

    def test_case_run_in_new_process(self):
        """Test whether a TestCase is run in a new process.

        * Runs a case with MultiprocessRunner.
        * Validates that the test ran.
        * Validates that the test was run in a different process (checking
            that a class member which is changed by the test remains unchanged
            in the current process).
        """
        BasicMultiprocessCase.pid_queue = self.pid_queue
        BasicMultiprocessCase.post_timeout_event = self.post_timeout_event

        MockSuite1.components = (BasicMultiprocessCase,)

        self.runner.run(MockSuite1)

        case_pid = self.pid_queue.get_nowait()

        self.assertNotEqual(case_pid, os.getpid(),
                            "%r wasn't run in a new process" % MockSuite1)

    def test_flow_run_in_new_process(self):
        """Test whether a TestFlow is run in a new process.

        * Runs a flow with MultiprocessRunner.
        * Validates that the test ran.
        * Validates that both the flow and its block ran in the same process.
        * Validates that the test-flow was run in a different process.
        """
        pid_queue = self.pid_queue
        RegisterInSetupFlow.common = {"pid_queue": pid_queue}
        MockSuite1.components = (RegisterInSetupFlow,)

        self.runner.run(MockSuite1)

        expected_registrations = 3  # Once for the flow and one per block
        pids = []
        while pid_queue.empty() is False:
            pids.append(pid_queue.get_nowait())

        self.assertEqual(len(pids), expected_registrations,
                         "Wrong amount of PID registractions %d instead of %d"
                         % (len(pids), expected_registrations))

        first_pid = pids[0]

        self.assertEqual(pids, [first_pid] * expected_registrations,
                         "The blocks and flow didn't run in the same process")

        self.assertNotEqual(first_pid, os.getpid(),
                            "The test flow wasn't run in a new process")

    def test_subprocess_killed(self):
        """Test that subprocess get killed when case ends.

        * Runs a test which opens a subprocess.
        * Validates that two processes were run.
        * Validates that both process got killed (worker and subprocess).
        """
        SubprocessCreationCase.pid_queue = self.pid_queue
        SubprocessCreationCase.post_timeout_event = self.post_timeout_event

        MockSuite1.components = (SubprocessCreationCase,)

        self.runner.run(MockSuite1)

        self.validate_test_processes(2)

    def test_keep_resources_in_worker(self):
        """Test that resources are kept in the worker's client.

        * Runs two tests with the same request.
        * Validates that only one instance of the resource was used.
        """
        ResourceIdRegistrationCase.pid_queue = self.pid_queue

        MockSuite1.components = (ResourceIdRegistrationCase,
                                 ResourceIdRegistrationCase)

        self.runner.run(MockSuite1)

        resources_locked = len(set(self.get_pids()))
        self.assertEqual(resources_locked, 1,
                         "Number of resource locks was %d instead of 1" %
                         resources_locked)


class TestMultipleWorkers(AbstractMultiprocessRunnerTest):
    """Test class for testing MultiprocessRunner."""

    PROCESSES_NUMBER = 2

    def test_not_share_worker_resources(self):
        """Test that resources are not shared between workers.

        * Runs two tests with the same request.
        * Validates that two instances of the resource was used.

        Note:
            Since the tests mock client doesn't really lock any resources
            both workers will get the same resource data, but will initiate
            different resource instance, which is good enough for the test.
        """
        ResourceIdRegistrationCase.pid_queue = self.pid_queue

        MockSuite1.components = (ResourceIdRegistrationCase,
                                 ResourceIdRegistrationCase)

        self.runner.run(MockSuite1)

        resources_locked = len(set(self.get_pids()))
        self.assertEqual(resources_locked, 2,
                         "Number of resource locks was %d instead of 2" %
                         resources_locked)


class TestMultiprocessRunnerSuite(unittest.TestSuite):
    """A test suite for multiprocess runner's tests."""
    TESTS = [TestMultiprocessRunner,
             TestMultipleWorkers]

    def __init__(self):
        """Construct the class."""
        super(TestMultiprocessRunnerSuite, self).__init__(
                            unittest.makeSuite(test) for test in self.TESTS)


if __name__ == '__main__':
    django.setup()
    colored_main(defaultTest='TestMultiprocessRunnerSuite')
