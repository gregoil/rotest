"""Multiprocess runner message handler."""
# pylint: disable=too-many-instance-attributes,too-few-public-methods
# pylint: disable=expression-not-assigned,too-many-arguments,unused-argument
from __future__ import absolute_import

from future.builtins import object

from rotest.common import core_log
from rotest.core.models.case_data import TestOutcome
from rotest.core.models.general_data import GeneralData
from rotest.management.common.parsers import DEFAULT_PARSER
from rotest.core.runners.multiprocess.common import (WrappedException,
                                                     get_item_by_id)
from rotest.management.common.messages import (StopTest,
                                               StartTest,
                                               AddResult,
                                               ShouldSkip,
                                               RunFinished,
                                               SetupFinished,
                                               StartTeardown,
                                               StopComposite,
                                               StartComposite,
                                               CloneResources,
                                               ShouldSkipReply)


class RunnerMessageHandler(object):
    """Multiprocess runner message handler.

    Updates the runner and the result object according to the workers messages.

    Attributes:
        runner (MultiprocessRunner): test runner object.
        result (Result): test result object.
        main_test (object): main test object.
        message_handlers (dict): maps worker messages to handling methods.
        result_event_handlers (dict): maps test outcomes to result methods.
    """
    def __init__(self, multiprocess_runner, result, main_test):
        """Initialize the message handler.

        Args:
            multiprocess_runner (MultiprocessRunner): test runner object.
            result (Result): test result object.
            main_test (object): main test object.
        """
        self.result = result
        self.main_test = main_test
        self.decoder = DEFAULT_PARSER()
        self.runner = multiprocess_runner

        self.result_event_handlers = {
            TestOutcome.ERROR: self.result.addError,
            TestOutcome.SKIPPED: self.result.addSkip,
            TestOutcome.FAILED: self.result.addFailure,
            TestOutcome.SUCCESS: self.result.addSuccess,
            TestOutcome.EXPECTED_FAILURE: self.result.addExpectedFailure,
            TestOutcome.UNEXPECTED_SUCCESS: self.result.addUnexpectedSuccess}

        self.message_handlers = {
            AddResult: self._handle_end_message,
            StopTest: self._handle_stop_message,
            StartTest: self._handle_start_message,
            ShouldSkip: self._handle_should_skip_message,
            SetupFinished: self._handle_setup_finished_message,
            StartTeardown: self._handle_start_teardown_message,
            StopComposite: self._handle_composite_stop_message,
            StartComposite: self._handle_composite_start_message,
            CloneResources: self._handle_update_resources_message}

    def handle_message(self, message):
        """Process given worker message.

        Handles messages from the workers' processes, and updates the
        manager & workers states accordingly.

        Args:
            message (str): worker message object.
        """
        message = self.decoder.decode(message)
        core_log.debug(message)

        if message.msg_id not in self.runner.workers_pool:
            core_log.warning('Ignoring restarted process %r message',
                             message.msg_id)
            return

        message_type = type(message)

        if message_type is RunFinished:
            self._handle_done_message(message)

        else:
            test = get_item_by_id(self.main_test, message.test_id)
            self.message_handlers[message_type](test, message)

    def _update_parent_start(self, test_item):
        """Recursively starts the parent test if needed.

        Checks the test's parent tests and if they did not start yet, it
        starts the parent test item and continues updating up.

        Note that the update occurs top to bottom, with the topmost test
        getting a 'start' message first.

        Args:
            test_item (object): test item to update its parent.
        """
        parent_test = test_item.parent

        if parent_test is None:
            return

        if parent_test.data.status != GeneralData.IN_PROGRESS:
            self._update_parent_start(parent_test)
            self.result.startComposite(parent_test)

    def _update_parent_stop(self, test_item):
        """Recursively stop the parent test if needed.

        Checks the test's sibling tests and if they are all finished,
        it stops the parent test item, then continues updating up.

        Note that the update occurs bottom to top, with the topmost
        test getting a 'stop' message last.

        Args:
            test_item (object): test item to update its parent.
        """
        parent_test = test_item.parent

        if parent_test is None:
            return

        if all(test_item.data.status == GeneralData.FINISHED
               for test_item in parent_test):

            self.result.stopComposite(parent_test)
            self._update_parent_stop(parent_test)

    def _handle_composite_start_message(self, test, message):
        """Handle StartComposite of a worker.

        Args:
            test (rotest.core.suite.TestSuite): test item to update.
            message (StartComposite): worker message object.
        """
        self._update_parent_start(test)
        self.result.startComposite(test)

    def _handle_should_skip_message(self, test, message):
        """Handle ShouldSkip of a worker.

        Args:
            test (object): test item to update.
            message (ShouldSkip): worker message object.
        """
        reply = self.decoder.encode(ShouldSkipReply(msg_id=message.msg_id,
                                    request_id=message.msg_id,
                                    should_skip=self.result.shouldSkip(test)))

        self.runner.workers_pool[message.msg_id].reply_queue.put(reply)

    def _handle_update_resources_message(self, test, message):
        """Handle UpdateResources of a worker.

        Args:
            test (object): test item to update.
            message (UpdateResources): worker message object.
        """
        test.locked_resources = message.resources
        self.result.updateResources(test)

    def _handle_start_message(self, test, message):
        """Handle StartTest of a worker.

        Args:
            test (object): test item to update.
            message (StartTest): worker message object.
        """
        # Since the logger is only created in the worker, we create it here
        self.result.startTest(test)
        if test.is_main:
            self.runner.update_worker(worker_pid=message.msg_id, test=test)
            self.runner.update_timeout(worker_pid=message.msg_id,
                                       timeout=test.TIMEOUT)

    def _handle_setup_finished_message(self, test, message):
        """Handle SetupFinished of a worker.

        Args:
            test (object): test item to update.
            message (StartTest): worker message object.
        """
        self.result.setupFinished(test)

    def _handle_start_teardown_message(self, test, message):
        """Handle StartTeardown of a worker.

        Args:
            test (object): test item to update.
            message (StartTest): worker message object.
        """
        self.result.startTeardown(test)

    def _handle_end_message(self, test, message):
        """Handle AddResult of a worker.

        Args:
            test (object): test item to update.
            message (AddResult): worker message object.
        """
        self.runner.update_timeout(worker_pid=message.msg_id, timeout=None)

        result_event_method = self.result_event_handlers[message.code]

        if message.info is not None:
            if message.code != TestOutcome.SKIPPED:
                result_info = (None, WrappedException(message.info), None)

            else:
                result_info = message.info

            result_event_method(test, result_info)

        else:
            result_event_method(test)

        # End the run by clearing the pending tests queue.
        if self.result.failfast and self.result.shouldStop:
            self.runner.clear_tests_queue()

    def _handle_stop_message(self, test, message):
        """Handle StopTest of a worker.

        Args:
            test (object): test item to update.
            message (StopTest): worker message object.
        """
        self.result.stopTest(test)
        if test.is_main:
            self._update_parent_stop(test)

    def _handle_composite_stop_message(self, test, message):
        """Handle StopComposite of a worker.

        Args:
            test (rotest.core.suite.TestSuite): test item to update.
            message (StopComposite): worker message object.
        """
        self.result.stopComposite(test)
        self._update_parent_stop(test)

    def _handle_done_message(self, message):
        """Handle RunFinished of a worker.

        Args:
            message (RunFinished): worker message object.
        """
        self.runner.finalize_worker(worker_pid=message.msg_id)
