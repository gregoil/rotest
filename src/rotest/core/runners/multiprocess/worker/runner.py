"""Multiprocess worker runner."""
# pylint: disable=too-many-arguments,invalid-name,protected-access
from rotest.core.runners.base_runner import BaseTestRunner
from rotest.core.runners.multiprocess.worker.result_handler import \
                                                            WorkerHandler


class WorkerRunner(BaseTestRunner):
    """Handle Rotest's worker test runner.

    In addition to the base test result capabilties it uses a queue
    object to notify the main runner on each result status change.

    Attributes:
        save_state (bool): determine if storing resources state is required.
            The behavior can be overridden using resource's save_state flag.
        config (object): config object, will be transfered to each test.
        run_delta (bool): determine whether to run only tests that failed the
            last run (according to the results DB).
        outputs (list): list of the output handlers' names.
        run_name (str): name of the current run.
        results_queue (multiprocessing.Queue): queue object used to transfer
            jobs results from all workers processes to the main runner process.
        reply_queue (multiprocessing.Queue): queue object used to transfer
            data from the main runner to this specific worker.
    """
    def __init__(self, save_state, config, run_delta, outputs,
                 run_name, results_queue, reply_queue, *args, **kwargs):

        super(WorkerRunner, self).__init__(save_state, config,
                                           run_delta, outputs, run_name,
                                           *args, **kwargs)

        self.reply_queue = reply_queue
        self.results_queue = results_queue

        self.queue_handler = WorkerHandler(self.reply_queue,
                                           self.results_queue)

        # Suppress stream write method
        self.stream.write = lambda *args, **kwargs: None

    def _makeResult(self):
        """Create test result object and add the queue handler to it.

        Returns:
            WorkerResult. notifying test result object.
        """
        super(WorkerRunner, self)._makeResult()

        # Add the queue handler to the list of the worker handlers.
        self.result.result_handlers.append(self.queue_handler)

        return self.result

    def _propagate_resource_manager(self, test_item):
        """Propagate the resource manager to all test items.

        Args:
            test_item (object): test object.
        """
        test_item._is_client_local = False
        test_item.resource_manager = self.resource_manager
        if test_item.IS_COMPLEX:
            for sub_item in test_item:
                self._propagate_resource_manager(sub_item)

    def execute(self, test_item):
        """Execute the given test item.

        Args:
            test_item (object): test object.

        Returns:
            RunData. test run data.
        """
        self.test_item = test_item
        self._propagate_resource_manager(test_item)
        return super(WorkerRunner, self).execute(test_item)
