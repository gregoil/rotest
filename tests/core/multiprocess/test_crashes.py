"""Test Rotest's multiprocess behavior on crashes."""
# pylint: disable=expression-not-assigned,invalid-name,not-callable
from __future__ import absolute_import

import sys
import unittest
from multiprocessing import Process, Queue, Event, active_children

import pytest
import psutil
from six.moves import queue
from future.builtins import range

from rotest.common import core_log
from rotest.core.runners.multiprocess.common import kill_process_tree
from rotest.core.runners.multiprocess.manager.runner import MultiprocessRunner

from tests.core.multiprocess.utils import TimeoutCase
from tests.core.utils import MockTestSuite, override_client_creator


class AbstractCrashTest(unittest.TestCase):
    """Abstract test for multiprocess module behavior upon processes death."""
    RUN_NAME = 'crash UT'
    WORKERS_NUMBER = 2
    QUEUE_GET_TIMEOUT = 2  # Seconds
    WORKERS_TIMEOUT = None  # Seconds
    RUNNER_JOIN_TIMEOUT = 4  # Seconds

    @classmethod
    def setUpClass(cls):
        """Set the server host to be the localhost.

        This will allow the resource manager server and the
        tests to use the same DB.
        """
        super(AbstractCrashTest, cls).setUpClass()

        override_client_creator()

    def setUp(self):
        """Prepare the runner and the workers processes.

        Constructs a test suite containing multiple tests, and creates a
        multiprocess runner to run in a different process.
        """
        self.worker_processes = None
        self.pid_queue = Queue()
        self.post_timeout_event = Event()

        TimeoutCase.TIMEOUT = self.WORKERS_TIMEOUT

        TimeoutCase.resources = ()
        TimeoutCase.pid_queue = self.pid_queue
        TimeoutCase.post_timeout_event = self.post_timeout_event

        # Creating more jobs than workers in order to validate recovery
        MockTestSuite.components = (TimeoutCase,) * self.WORKERS_NUMBER * 2

        runner = MultiprocessRunner(config=None,
                                    outputs=[],
                                    run_delta=False,
                                    save_state=False,
                                    enable_debug=False,
                                    run_name=self.RUN_NAME,
                                    workers_number=self.WORKERS_NUMBER)

        self.runner_process = Process(target=runner.run, args=(MockTestSuite,))

    def tearDown(self):
        """Cleanup the runner and its workers if they are still alive."""
        active_children()  # Join all done processes.

        core_log.debug("Waiting for runner process to end")
        self.runner_process.join(timeout=self.RUNNER_JOIN_TIMEOUT)

        try:
            core_log.debug("Killing runner process tree")
            process = psutil.Process(self.runner_process.pid)
            kill_process_tree(process)

        except psutil.NoSuchProcess:
            core_log.debug("Process %r not found", self.runner_process.pid)


@pytest.mark.skipif(sys.platform == "win32",
                    reason="Test isn't runnable on Windows")
class RunnerCrashTest(AbstractCrashTest):
    """Test workers behavior upon runner process death."""
    WORKERS_TIMEOUT = 2  # Seconds
    WORKER_SUICIDE_TIMEOUT = 4  # Seconds
    RUNNER_KILLING_TIMEOUT = 4  # Seconds

    def test_runner_crash(self):
        """Test that workers kill themselves if their runner died."""
        core_log.debug("Starting runner process")
        self.runner_process.start()

        core_log.debug("Waiting for the workers to start")
        workers_pids = [self.pid_queue.get(timeout=self.QUEUE_GET_TIMEOUT)
                        for _ in range(self.WORKERS_NUMBER)]

        runner_process = psutil.Process(self.runner_process.pid)
        self.worker_processes = runner_process.children()

        core_log.debug("Killing the runner process")
        self.runner_process.terminate()
        runner_process.wait(timeout=self.RUNNER_KILLING_TIMEOUT)

        core_log.debug("Waiting for all active workers to die")
        for worker in self.worker_processes:
            worker.wait(timeout=self.WORKER_SUICIDE_TIMEOUT)

        core_log.debug("Validating no new workers were created")
        self.assertRaises(queue.Empty, self.pid_queue.get_nowait)

        core_log.debug("Validating the number of cases ran")
        self.assertEqual(len(workers_pids), self.WORKERS_NUMBER,
                         "Number of cases ran was supposed to be %d"
                         " Got %d instead" % (self.WORKERS_NUMBER,
                                              len(workers_pids)))


@pytest.mark.skipif(sys.platform == "win32",
                    reason="Test isn't runnable on Windows")
class WorkerCrashTest(AbstractCrashTest):
    """Test runner behavior upon workers processes death."""
    WORKERS_TIMEOUT = 10  # Seconds
    QUEUE_GET_TIMEOUT = 5

    def test_worker_crash(self):
        """Test if multiprocess runner recover crashed workers."""
        core_log.debug("Starting runner process")
        self.runner_process.start()

        core_log.debug("Waiting for the workers to start")
        workers_pids = [self.pid_queue.get(timeout=self.QUEUE_GET_TIMEOUT)
                        for _ in range(self.WORKERS_NUMBER)]

        core_log.debug("Validating no extra workers were created")
        self.assertRaises(queue.Empty, self.pid_queue.get_nowait)

        core_log.debug("Killing all active workers")
        for worker_pid in workers_pids:
            worker_process = psutil.Process(worker_pid)
            worker_process.kill()
            worker_process.wait()

        core_log.debug("Waiting for the alternative workers to start")
        new_workers_pids = [self.pid_queue.get(timeout=self.QUEUE_GET_TIMEOUT)
                            for _ in range(self.WORKERS_NUMBER)]

        core_log.debug("Validating no extra workers were created")
        self.assertRaises(queue.Empty, self.pid_queue.get_nowait)

        core_log.debug("Validating new workers differs from older workers")
        self.assertNotEqual(workers_pids, new_workers_pids,
                            "Dead workers should have been replaced")


if __name__ == '__main__':
    unittest.main()
