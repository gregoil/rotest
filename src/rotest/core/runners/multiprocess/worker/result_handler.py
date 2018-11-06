"""Multiprocess worker result handler."""
# pylint: disable=protected-access
from __future__ import absolute_import
import os
import time

from future.utils import iteritems

from rotest.core.models.case_data import TestOutcome
from rotest.management.common.parsers import DEFAULT_PARSER
from rotest.core.result.handlers.abstract_handler import AbstractResultHandler
from rotest.management.common.messages import (StopTest,
                                               AddResult,
                                               StartTest,
                                               ShouldSkip,
                                               RunFinished,
                                               SetupFinished,
                                               StartTeardown,
                                               StopComposite,
                                               StartComposite,
                                               CloneResources)


class WorkerHandler(AbstractResultHandler):
    """Update the main process about test events via queue.

    Attributes:
        results_queue (multiprocessing.Queue): queue object used to transfer
            jobs results from all workers processes to the main runner process.
        reply_queue (multiprocessing.Queue): queue object used to transfer
            data from the main runner to this specific worker.

        REPLY_TIMEOUT (number): maximal time to wait for the manager replies.
    """
    REPLY_TIMEOUT = 60  # seconds

    def __init__(self, reply_queue, results_queue, *args, **kwargs):
        """Initialize result handler and save the result queue.

        Args:
            results_queue (multiprocessing.Queue): queue object used to
                transfer test events to the main runner process.
            reply_queue (multiprocessing.Queue): queue object used to transfer
                data from the main runner to this specific worker.
        """
        super(WorkerHandler, self).__init__()
        self.parser = DEFAULT_PARSER()
        self.worker_pid = os.getpid()
        self.reply_queue = reply_queue
        self.results_queue = results_queue

    def send_message(self, message):
        """Put a message in the results queue.

        Args:
            message (collections.namedtuple): message to send.
        """
        self.results_queue.put(self.parser.encode(message))
        # Wait for the lock to be released on both sides of the queue.
        time.sleep(0.1)

    def get_message(self, timeout=REPLY_TIMEOUT):
        """Waits for a message in the reply queue.

        Args:
            timeout (number): waiting timeout.
        """
        message = self.reply_queue.get(timeout=timeout, block=True)
        return self.parser.decode(message)

    def start_test(self, test):
        """Notify the manager about the starting of a test run via queue."""
        self.send_message(StartTest(msg_id=self.worker_pid,
                                    test_id=test.identifier))

    def should_skip(self, test):
        """Check if the test should be skipped.

        Args:
            test (object): test item instance.

        Returns:
            str. skip reason if the test should be skipped, None otherwise.
        """
        self.send_message(ShouldSkip(msg_id=self.worker_pid,
                                     test_id=test.identifier))
        skip_reason = self.get_message().should_skip
        return skip_reason

    def setup_finished(self, test):
        """Notify the manager about the finish of a test setup via queue."""
        self.send_message(SetupFinished(msg_id=self.worker_pid,
                                        test_id=test.identifier))

    def start_teardown(self, test):
        """Notify the manager about the start of a test teardown via queue."""
        self.send_message(StartTeardown(msg_id=self.worker_pid,
                                        test_id=test.identifier))

    def update_resources(self, test):
        """Called once after locking the tests resources.

        Args:
            test (object): test item instance.
        """
        test_resources = {
            request_name: resource
            for request_name, resource in iteritems(test.locked_resources)
            if resource.DATA_CLASS is not None
        }

        self.send_message(CloneResources(msg_id=self.worker_pid,
                                         test_id=test.identifier,
                                         resources=test_resources))

    def stop_test(self, test):
        """Notify the manager about the finish of a test run via queue.

        Args:
            test (object): test item instance.
        """
        self.send_message(StopTest(msg_id=self.worker_pid,
                                   test_id=test.identifier))

    def start_composite(self, test):
        """Called when the given TestSuite is about to be run.

        Args:
            test (rotest.core.suite.TestSuite): test item instance.
        """
        self.send_message(StartComposite(msg_id=self.worker_pid,
                                         test_id=test.identifier))

    def stop_composite(self, test):
        """Called when the given TestSuite has been run.

        Args:
            test (rotest.core.suite.TestSuite): test item instance.
        """
        self.send_message(StopComposite(msg_id=self.worker_pid,
                                        test_id=test.identifier))

    def add_success(self, test):
        """Notify the manager about a success via queue."""
        self.send_message(AddResult(msg_id=self.worker_pid,
                                    test_id=test.identifier,
                                    code=TestOutcome.SUCCESS,
                                    info=None))

    def add_error(self, test, exception_string):
        """Notify the manager about an error via queue.

        This also wraps the exception so the error data could be passed
        through the queue.
        """
        self.send_message(AddResult(msg_id=self.worker_pid,
                                    test_id=test.identifier,
                                    code=TestOutcome.ERROR,
                                    info=exception_string))

    def add_failure(self, test, exception_string):
        """Notify the manager about a failure via queue.

        This also wraps the exception so the error data could be passed
        through the queue.
        """
        self.send_message(AddResult(msg_id=self.worker_pid,
                                    test_id=test.identifier,
                                    code=TestOutcome.FAILED,
                                    info=exception_string))

    def add_skip(self, test, reason):
        """Notify the manager about a skip via queue."""
        self.send_message(AddResult(msg_id=self.worker_pid,
                                    test_id=test.identifier,
                                    code=TestOutcome.SKIPPED,
                                    info=reason))

    def add_expected_failure(self, test, exception_string):
        """Notify the manager about an expected failure via queue.

        This also wraps the exception so the error data could be passed
        through the queue.
        """
        self.send_message(AddResult(msg_id=self.worker_pid,
                                    test_id=test.identifier,
                                    code=TestOutcome.EXPECTED_FAILURE,
                                    info=exception_string))

    def add_unexpected_success(self, test):
        """Notify the manager about an unexpected success via queue."""
        self.send_message(AddResult(msg_id=self.worker_pid,
                                    test_id=test.identifier,
                                    code=TestOutcome.UNEXPECTED_SUCCESS,
                                    info=None))

    def finish_run(self):
        """Called when the the worker has finished running tests."""
        self.send_message(RunFinished(msg_id=self.worker_pid))
