"""Tests results handling interface."""
# pylint: disable=invalid-name,too-few-public-methods,arguments-differ
# pylint: disable=too-many-arguments,dangerous-default-value
from unittest.result import TestResult
import pkg_resources

from rotest.common import core_log
from rotest.core.models.case_data import TestOutcome
from rotest.common.log import get_test_logger, get_tree_path
from rotest.core.flow_component import AbstractFlowComponent


def get_result_handlers():
    return {entry_point.name: entry_point.load()
            for entry_point in
            pkg_resources.iter_entry_points("rotest.result_handlers")}


class Result(TestResult):
    """Manager class for handling tests' run information.

    Attributes:
        DEFAULT_OUTPUTS (tuple): default output handlers' names.
        OUTPUTS_HANDLERS (dict): converts from an output handler's name to
            its class.
        result_handlers (list): the run's output handler instances.
        main_test (object): the main test instance (e.g. TestSuite instance
            or TestFlow instance).
    """
    DEFAULT_OUTPUTS = ("tree", "excel")

    def __init__(self, stream=None, descriptions=None,
                 outputs=DEFAULT_OUTPUTS, main_test=None):

        TestResult.__init__(self, stream, descriptions)

        self.main_test = main_test

        all_result_handlers = get_result_handlers()

        self.result_handlers = [
            all_result_handlers[result_handler_name](
                stream=stream,
                main_test=main_test,
                descriptions=descriptions)
            for result_handler_name in outputs
        ]

    def startTestRun(self):
        """Called once before any tests are executed."""
        super(Result, self).startTestRun()

        core_log.info("Test run has started")

        for result_handler in self.result_handlers:
            result_handler.start_test_run()

    def startTest(self, test):
        """Called when the given test is about to be run.

        Args:
            test (object): test item instance.
        """
        if not isinstance(test, AbstractFlowComponent) or test.is_main:
            super(Result, self).startTest(test)

        test.logger = get_test_logger(get_tree_path(test), test.work_dir)
        test.logger.info("Test %r has started running", test.data)
        test.override_resource_loggers()
        test.start()

        for result_handler in self.result_handlers:
            result_handler.start_test(test)

    def setupFinished(self, test):
        """Called when the given test finished setting up.

        Args:
            test (object): test item instance.
        """
        test.logger.info("Test %r finished setup", test.data)
        for result_handler in self.result_handlers:
            result_handler.setup_finished(test)

    def startTeardown(self, test):
        """Called when the given test is starting its teardown.

        Args:
            test (object): test item instance.
        """
        test.logger.info("Test %r started teardown", test.data)
        for result_handler in self.result_handlers:
            result_handler.start_teardown(test)

    def shouldSkip(self, test):
        """Check if the test should be skipped.

        The result is based on querying all the test handlers. If any of the
        handler answers the query positively, the test skips.

        Args:
            test (object): test item instance.

        Returns:
            str. Skip reason if the test should be skipped, None otherwise.
        """
        for test_handler in self.result_handlers:
            query_result = test_handler.should_skip(test)
            if query_result is not None:
                test.logger.debug("Skipping test %r according to handler %r",
                                  test.data.name, test_handler.NAME)
                return query_result

        return None

    def updateResources(self, test):
        """Called once after locking the tests resources.

        Args:
            test (object): test item instance.
        """
        test.logger.debug("Saving %r's resources", test.data)
        for result_handler in self.result_handlers:
            result_handler.update_resources(test)

    def stopTest(self, test):
        """Called when the given test has been run.

        Args:
            test (object): test item instance.
        """
        if not isinstance(test, AbstractFlowComponent) or test.is_main:
            super(Result, self).stopTest(test)

        test.logger.debug("Test %r has stopped running", test.data)

        test.data.end()
        test.release_resource_loggers()
        for result_handler in self.result_handlers:
            result_handler.stop_test(test)

        # In order to avoid having too many open files we close the log file
        # handlers at the end of each test.
        handlers = test.logger.handlers[:]
        for handler in handlers:
            handler.close()
            test.logger.removeHandler(handler)

    def startComposite(self, test):
        """Called when the given TestSuite is about to be run.

        This method, unlike 'startTest', does not call unittest TestResult's
        'startTest', in order to avoid wrong test counting and treating
        TestSuites as the actual tests.

        Args:
            test (rotest.core.suite.TestSuite): test item instance.
        """
        core_log.info("Test %r has started running", test.data)
        test.start()

        for result_handler in self.result_handlers:
            result_handler.start_composite(test)

    def stopComposite(self, test):
        """Called when the given TestSuite has been run.

        This method, unlike 'stopTest', does not call unittest TestResult's
        'stopTest', in order to avoid output redirections and treating
        TestSuites as the actual tests.

        Args:
            test (rotest.core.suite.TestSuite): test item instance.
        """
        core_log.debug("Test %r has stopped running", test.data)
        sub_values = [sub_test.data.success for sub_test in test
                      if sub_test.data.success is not None]

        if len(sub_values) > 0:
            test.data.success = all(sub_values)

        test.data.end()

        for result_handler in self.result_handlers:
            result_handler.stop_composite(test)

    def stopTestRun(self):
        """Called once after all tests are executed."""
        super(Result, self).stopTestRun()

        core_log.info("Test run has finished")

        for result_handler in self.result_handlers:
            result_handler.stop_test_run()

    def addSuccess(self, test):
        """Called when a test has completed successfully.

        Args:
            test (object): test item instance.
        """
        if test.data.exception_type is not None:
            return

        if not isinstance(test, AbstractFlowComponent) or test.is_main:
            super(Result, self).addSuccess(test)

        test.logger.info("Test %r ended successfully", test.data)
        test.end(test_outcome=TestOutcome.SUCCESS)

        for result_handler in self.result_handlers:
            result_handler.add_success(test)

    def addSkip(self, test, reason):
        """Called when a test is skipped.

        Args:
            test (object): test item instance.
            reason (str): skip reason description.
        """
        if not isinstance(test, AbstractFlowComponent) or test.is_main:
            super(Result, self).addSkip(test, reason)

        test.logger.warning("Test %r skipped, reason %r", test.data, reason)
        test.end(test_outcome=TestOutcome.SKIPPED, details=reason)

        for result_handler in self.result_handlers:
            result_handler.add_skip(test, reason)

    def addFailure(self, test, err):
        """Called when an error has occurred.

        Args:
            test (object): test item instance.
            err (tuple): tuple of values as returned by sys.exc_info().
        """
        if not isinstance(test, AbstractFlowComponent) or test.is_main:
            super(Result, self).addFailure(test, err)

        exception_string = self._exc_info_to_string(err, test)
        test.logger.error("Test %r ended in failure: %s",
                          test.data, exception_string)
        test.end(test_outcome=TestOutcome.FAILED, details=exception_string)

        for result_handler in self.result_handlers:
            result_handler.add_failure(test, exception_string)

    def addError(self, test, err):
        """Called when an error has occurred.

        Args:
            test (object): test item instance.
            err (tuple): tuple of values as returned by sys.exc_info().
        """
        if not isinstance(test, AbstractFlowComponent) or test.is_main:
            super(Result, self).addError(test, err)

        exception_string = self._exc_info_to_string(err, test)
        test.logger.critical("Test %r ended in error: %s",
                             test.data, exception_string)
        test.end(test_outcome=TestOutcome.ERROR, details=exception_string)

        for result_handler in self.result_handlers:
            result_handler.add_error(test, exception_string)

    def addExpectedFailure(self, test, err):
        """Called when an expected failure/error occurred.

        Args:
            test (object): test item instance.
            err (tuple): tuple of values as returned by sys.exc_info().
        """
        if not isinstance(test, AbstractFlowComponent) or test.is_main:
            super(Result, self).addExpectedFailure(test, err)

        exception_string = self._exc_info_to_string(err, test)

        test.logger.info("Test %r ended in an expected failure: %s",
                         test.data, exception_string)
        test.end(test_outcome=TestOutcome.EXPECTED_FAILURE,
                 details=exception_string)

        for result_handler in self.result_handlers:
            result_handler.add_expected_failure(test, exception_string)

    def addUnexpectedSuccess(self, test):
        """Called when a test was expected to fail, but succeed.

        Args:
            test (object): test item instance.
            err (tuple): tuple of values as returned by sys.exc_info().
        """
        if not isinstance(test, AbstractFlowComponent) or test.is_main:
            super(Result, self).addUnexpectedSuccess(test)

        test.logger.error("Test %r ended in an unexpected success", test.data)
        test.end(test_outcome=TestOutcome.UNEXPECTED_SUCCESS)

        for result_handler in self.result_handlers:
            result_handler.add_unexpected_success(test)

    def printErrors(self):
        """Called by TestRunner after test run."""
        super(Result, self).printErrors()

        for result_handler in self.result_handlers:
            result_handler.print_errors(self.testsRun, self.errors,
                                        self.skipped, self.failures,
                                        self.expectedFailures,
                                        self.unexpectedSuccesses)
