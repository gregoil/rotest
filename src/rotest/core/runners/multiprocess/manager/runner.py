"""Rotest's multiprocess test runner."""
# pylint: disable=expression-not-assigned
# pylint: disable=too-many-instance-attributes,too-many-arguments
from __future__ import absolute_import

import os
import time
import datetime
from multiprocessing import Queue

import six
from six.moves import queue
from future.builtins import range
from future.utils import itervalues

from rotest.common import core_log
from rotest.core.case import TestCase
from rotest.core.flow import TestFlow
from rotest.core.suite import TestSuite
from rotest.core.result.monitor import AbstractMonitor
from rotest.core.result.result import get_result_handlers
from rotest.core.runners.base_runner import BaseTestRunner
from rotest.core.runners.multiprocess.worker.process import WorkerProcess
from rotest.core.runners.multiprocess.manager.message_handler import \
                                                        RunnerMessageHandler


class MultiprocessRunner(BaseTestRunner):
    """Rotest's multiprocess test runner.

    Manages workers process pool, assigns jobs via requests' queue and gets
    results via results' queue.

    Attributes:
        DEFAULT_TIMEOUT (number): default seconds to wait for workers messages.
        PROCESS_DEATH_TIMEOUT (number): seconds to wait for death of workers.
        DEFAULT_WORKERS_NUMBER (number): default number of workers for tests.

        save_state (bool): determine if storing resources state is required.
            The behavior can be overridden using resource's save_state flag.
        skip_init (bool): True to skip resources initialization and validation.
        config (object): config object, will be transfered to each test.
        run_delta (bool): determine whether to run only tests that failed the
            last run (according to the results DB).
        outputs (list): list of the output handlers' names.
        run_name (str): name of the current run.
        workers_number (number): number of worker processes.
        requests_queue (multiprocessing.Queue): queue object used to transfer
            jobs to all workers processes from the main runner process.
        results_queue (multiprocessing.Queue): queue object used to transfer
            jobs results from all workers processes to the main runner process.
        message_handlers (dict): converts from a message class to its handler.
        result_event_handlers (dict): converts from outcome codes to the
            result's event handler.
    """
    DEFAULT_TIMEOUT = 1
    PROCESS_DEATH_TIMEOUT = 2
    DEFAULT_WORKERS_NUMBER = 2

    def __init__(self, save_state, config, run_delta, outputs, run_name,
                 enable_debug, skip_init=False,
                 workers_number=DEFAULT_WORKERS_NUMBER, *args, **kwargs):
        """Initialize the multiprocess test runner.

        Initializes the workers pool, the request & results queues.
        """
        super(MultiprocessRunner, self).__init__(save_state=save_state,
                                                 config=config,
                                                 run_delta=run_delta,
                                                 outputs=outputs,
                                                 skip_init=skip_init,
                                                 run_name=run_name,
                                                 enable_debug=enable_debug,
                                                 *args, **kwargs)
        self.workers_pool = {}

        self.results_queue = None
        self.requests_queue = None
        self.message_handler = None

        self.finished_workers = 0
        self.workers_number = workers_number
        output_handlers = get_result_handlers()

        # Separate monitors from regular output handlers
        self.monitors = [handler_name for handler_name in self.outputs
                         if issubclass(output_handlers[handler_name],
                                       AbstractMonitor)]

        self.outputs = [handler_name for handler_name in self.outputs
                        if handler_name not in self.monitors]

    def queue_test_jobs(self, test_item):
        """Queue all the test cases DB identifiers.

        Goes over the test item's sub tests recursively and adds
        each case identifier to the jobs queue.

        Args:
            test_item (object): test object.
        """
        if isinstance(test_item, TestSuite):
            for sub_test in test_item:
                self.queue_test_jobs(sub_test)

        elif isinstance(test_item, (TestCase, TestFlow)):
            self.requests_queue.put(test_item.identifier)

    @staticmethod
    def create_resource_manager():
        """Suppress creating resource manager so each test would create one.

        Returns:
            ClientResourceManager. a resource manager client.
        """
        return None

    def initialize_worker(self):
        """Create and start a new worker process and add it to the pool."""
        worker = WorkerProcess(config=self.config,
                               reply_queue=Queue(),
                               parent_id=os.getpid(),
                               failfast=self.failfast,
                               run_name=self.run_name,
                               root_test=self.test_item,
                               run_delta=self.run_delta,
                               skip_init=self.skip_init,
                               save_state=self.save_state,
                               output_handlers=self.monitors,
                               results_queue=self.results_queue,
                               requests_queue=self.requests_queue)

        worker.resource_manager = \
            super(MultiprocessRunner, self).create_resource_manager()

        worker.start()

        self.workers_pool[worker.pid] = worker

    def update_worker(self, worker_pid, test):
        """Update the worker properties.

        Args:
            worker_pid (number): worker's process id.
            test (object): the worker's current test.
        """
        worker = self.workers_pool[worker_pid]
        core_log.debug("Updating worker %r to run test %r", worker, test)
        worker.test = test

    def update_timeout(self, worker_pid, timeout):
        """Update the worker timeout.

        Args:
            worker_pid (number): worker's process id.
            timeout (number): a timeout to be applied on the worker run (in
                seconds). If None is passed, no timeout will be applied.
        """
        worker = self.workers_pool[worker_pid]

        core_log.debug("Updating worker %r to use timeout %r", worker, timeout)
        worker.start_time = datetime.datetime.now()
        worker.timeout = timeout

    def finalize_worker(self, worker_pid):
        """Finalize the worker.

        * Updates finished workers counter.
        * Removes worker from workers pool.
        * Terminates the worker process.

        Args:
            worker_pid (number): worker's process id.
        """
        self.finished_workers += 1
        worker_to_terminate = self.workers_pool.pop(worker_pid)
        worker_to_terminate.terminate()

    def clear_tests_queue(self):
        """Empty the pending requests queue, preventing the tests' run."""
        core_log.debug('Clearing pending tests')
        try:
            while True:
                self.requests_queue.get(block=False)

        except queue.Empty:
            pass

    def restart_worker(self, worker, reason):
        """Terminate the given worker and start a replacement worker.

        Note:
            Terminated tests will result in 'Error', and won't run again.

        Args:
            worker (WorkerProcess): terminated worker's process.
            reason (str): the reason for the reset.
        """
        core_log.info("Worker %r is dead. Restarting", worker)

        # Check if the worker was restarted before a test started
        if worker.test is not None:
            if six.PY2:
                self.result.addError(worker.test, (RuntimeError, reason, None))

            elif six.PY3:
                self.result.addError(worker.test, (RuntimeError,
                                                   RuntimeError(reason),
                                                   None))

            self.result.stopComposite(worker.test.parent)

        worker_to_terminate = self.workers_pool.pop(worker.pid)
        worker_to_terminate.terminate()

        # Waiting for the old process to die before creating a new one
        time.sleep(self.PROCESS_DEATH_TIMEOUT)

        self.initialize_worker()

    def initialize(self, test_class):
        """Initialize the test runner.

        Creates the workers processes and starts them.
        """
        super(MultiprocessRunner, self).initialize(test_class)

        self.results_queue = Queue()
        self.requests_queue = Queue()

    def finalize(self):
        """Finalize the test runner.

        Goes over the active workers, terminates and joins them.
        """
        for worker in itervalues(self.workers_pool):
            worker.terminate()

        self.finished_workers = 0

    def get_timeout(self):
        """Return the worker's joint timeout.

        The joint timeout is the minimum value of all the worker's
        remaining timeouts.

        Returns:
            number. joint timeout.
            None. if no timeout was set.
        """
        current_datetime = datetime.datetime.now()

        minimum_timeout = self.DEFAULT_TIMEOUT

        for worker in itervalues(self.workers_pool):
            if worker.timeout is not None:
                test_duration = current_datetime - worker.start_time
                remaining_time = worker.timeout - test_duration.total_seconds()

                if remaining_time < minimum_timeout:
                    minimum_timeout = remaining_time

        return minimum_timeout

    def handle_workers_events(self):
        """Identify which workers timed out or died and reset them.

        Goes over the active workers and for each worker:

        * Validate worker process is alive.
        * Validate  running time doesn't exceeds its given timeout.
        * If one of the validations fails, reset the worker.
        """
        current_datetime = datetime.datetime.now()

        # Note: Using items() because workers_pool may change during iteration.
        for pid, worker in list(self.workers_pool.items()):
            if not worker.is_alive():
                self.restart_worker(
                    worker=worker,
                    reason='Worker %r has died unexpectedly' % pid)

            elif worker.timeout is not None:
                timeout = worker.timeout
                test_duration = current_datetime - worker.start_time
                test_duration = test_duration.total_seconds()

                if test_duration > timeout:
                    self.restart_worker(
                        worker=worker,
                        reason='Worker %r timed out (%r > %r)' %
                               (pid, test_duration, timeout))

    def execute(self, test_item):
        """Execute the given test item.

        * Starts the main test.
        * Queues sub cases identifiers into the request queue.
        * Waits on the results queue for test results while
          handling timed out tests, and updating console.
        * Once all workers finished working return the run data.

        Args:
            test_item (object): test object.

        Returns:
            RunData. test run data.
        """
        result = self._makeResult()

        self.message_handler = RunnerMessageHandler(result=result,
                                                    main_test=self.test_item,
                                                    multiprocess_runner=self)
        result.startTestRun()

        core_log.debug('Queuing %r tests jobs', self.test_item.data.name)
        self.queue_test_jobs(self.test_item)

        core_log.debug('Creating %d workers processes', self.workers_number)
        for _ in range(self.workers_number):
            self.initialize_worker()

        while self.finished_workers < self.workers_number:

            try:
                message = self.results_queue.get(timeout=self.get_timeout())
                self.message_handler.handle_message(message)

            except queue.Empty:
                self.handle_workers_events()

        result.stopTestRun()
        result.printErrors()

        return self.test_item.data.run_data
