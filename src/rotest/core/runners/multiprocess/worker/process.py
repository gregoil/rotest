"""Multiprocess worker process."""
# pylint: disable=invalid-name,too-many-arguments,too-many-instance-attributes
from __future__ import absolute_import
from multiprocessing import Process

import psutil
from six.moves import queue

from rotest.common import core_log
from rotest.core.runners.multiprocess.worker.runner import WorkerRunner
from rotest.core.runners.multiprocess.common import (get_item_by_id,
                                                     kill_process_tree)


class WorkerProcess(Process):
    """Process that run tests.

    The process is built with all the manager's test runner properties,
    including the root test item. Once the process is started, the worker
    creates its own test runner instance. Then, it pulls job requests from
    queue one by one, executes them and notifies the manager via queue.

    Attributes:
        save_state (bool): determine if storing resources state is required.
            The behavior can be overridden using resource's save_state flag.
        config (object): config object, will be transfered to each test.
        run_delta (bool): determine whether to run only tests that failed the
            last run (according to the results DB).
        run_name (str): name of the current run.
        requests_queue (multiprocessing.Queue): queue object used to transfer
            jobs to all workers processes from the main runner process.
        reply_queue (multiprocessing.Queue): queue object used to transfer
            data from the main runner to this specific worker.
        results_queue (multiprocessing.Queue): queue object used to transfer
            jobs results from all workers processes to the main runner process.
        root_test (object): test object of the main test.
        failfast (bool): whether to stop the run on the first failure.
        parent_id (number): the id of the parent process.
        test (object): test instance which is ran by the worker.
        timeout (number): timeout which will cause the current test to stop
            if it passes it.
        start_time (datetime.datetime): the start time of the current test.
        skip_init (bool): True to skip resources initialization and validation.
        output_handlers (list): output handlers for the worker's runner.
    """

    def __init__(self, save_state, config, run_delta, run_name, requests_queue,
                 reply_queue, results_queue, root_test, failfast, parent_id,
                 skip_init, output_handlers, *args, **kwargs):

        core_log.debug('Initializing test worker')
        super(WorkerProcess, self).__init__()

        # Current test instance, timeout and starting time
        # They will be managed outside of the process
        self.test = None
        self.timeout = None
        self.start_time = None
        self.resource_manager = None

        self.root_test = root_test
        self.reply_queue = reply_queue
        self.results_queue = results_queue
        self.requests_queue = requests_queue
        self.output_handlers = output_handlers

        self.config = config
        self.run_name = run_name
        self.failfast = failfast
        self.parent_id = parent_id
        self.run_delta = run_delta
        self.skip_init = skip_init
        self.save_state = save_state

    def terminate(self):
        """Terminate the worker process and all of its subprocesses."""
        core_log.debug("Ending process %r", self.pid)
        try:
            process = psutil.Process(self.pid)
            kill_process_tree(process)

        except psutil.NoSuchProcess:
            core_log.debug("Process %r not found", self.pid)

    def assert_runner_is_alive(self):
        """Validate that the runner process is alive. If not - kill the worker.

        If the worker's parent process id changes it means that the manager
        process died. In that case the worker should die.
        """
        if self.parent_id != psutil.Process(self.pid).ppid():
            core_log.warning('Worker %r parent changed, terminating', self.pid)
            self.terminate()

    def _get_tests(self):
        """Try to get a new test from the pending tests queue.

        Returns:
            object. a pending test, or None if queue is empty.
        """
        try:
            return self.requests_queue.get(block=False)

        except queue.Empty:
            return None

    def run(self):
        """Initialize runner and run tests from queue.

        Creates a test runner then pulls requests from queue,
        executes them and notifies to the runner using results queue.
        Once done it notifies about its termination to the manager process.
        """
        core_log.debug('Worker %r started working', self.pid)

        runner = WorkerRunner(config=self.config,
                              enable_debug=False,
                              failfast=self.failfast,
                              run_name=self.run_name,
                              run_delta=self.run_delta,
                              skip_init=self.skip_init,
                              save_state=self.save_state,
                              outputs=self.output_handlers,
                              reply_queue=self.reply_queue,
                              results_queue=self.results_queue)

        runner.resource_manager = self.resource_manager

        try:
            for test_id in iter(self._get_tests, None):
                self.assert_runner_is_alive()

                test = get_item_by_id(self.root_test, test_id)
                core_log.debug('Worker %r is running %r',
                               self.pid, test.data.name)
                runner.execute(test)
                core_log.debug('Worker %r done with %r',
                               self.pid, test.data.name)

        finally:
            if (self.resource_manager is not None and
                    self.resource_manager.is_connected()):
                runner.resource_manager.disconnect()

            core_log.debug('Worker %r finished working', self.pid)
            runner.queue_handler.finish_run()
