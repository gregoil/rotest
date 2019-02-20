"""Stream output handler."""
# pylint: disable=invalid-name,too-few-public-methods,arguments-differ
# pylint: disable=too-many-arguments,super-init-not-called
from __future__ import absolute_import
from rotest.common.constants import GREEN, YELLOW, RED, BOLD, CYAN, BLUE
from rotest.core.result.handlers.stream.base_handler import BaseStreamHandler


class EventStreamHandler(BaseStreamHandler):
    """Stream event handler.

    Overrides result handler's methods to print each event change in
    the main result object to the given stream.
    """
    NAME = 'full'

    def start_test_run(self):
        """Write the test run start to the stream."""
        self.stream.writeln('Tests Run Started', None, BOLD)

    def start_test(self, test):
        """Write the test start to the stream.

        Args:
            test (TestSuite / TestCase): test item instance.
        """
        self.stream.writeln('Test %s Started' % test.data.name)

    def stop_test(self, test):
        """Log the test stop to the stream.

        Args:
            test (TestSuite / TestCase): test item instance.
        """
        self.stream.writeln('Test %s Finished' % test.data.name)

    def start_composite(self, test):
        """Called when the given TestSuite is about to be run.

        Args:
            test (TestSuite / TestCase): test item instance.
        """
        self.start_test(test)

    def stop_composite(self, test):
        """Called when the given TestSuite has been run.

        Args:
            test (TestSuite / TestCase): test item instance.
        """
        self.stop_test(test)

    def stop_test_run(self):
        """Write the test run end to the stream."""
        self.stream.writeln('Tests Run Finished', None, BOLD)

    def add_success(self, test, msg):
        """Write the test success to the stream.

        Args:
            test (TestCase): test item instance.
            msg (str): success message.
        """
        self.stream.writeln('Success: %s' % test, GREEN)
        if msg is not None:
            self.write_details(msg, color=GREEN)

    def add_skip(self, test, reason):
        """Write the test skip to the stream.

        Args:
            test (TestCase): test item instance.
            reason (str): skip reason description.
        """
        self.stream.writeln('Skip: %s' % test, YELLOW)
        self.write_details(reason, color=YELLOW)

    def add_failure(self, test, exception_str):
        """Write the failure to the stream.

        Args:
            test (TestCase): test item instance.
            exception_str (str): exception traceback string.
        """
        self.stream.writeln('Failure: %s' % test, RED)
        self.write_details(exception_str, color=RED)

    def add_error(self, test, exception_str):
        """Write the error to the stream.

        Args:
            test (TestCase): test item instance.
            exception_str (str): exception traceback string.
        """
        self.stream.writeln('Error: %s' % test, RED, BOLD)
        self.write_details(exception_str, 0, RED, BOLD)

    def add_expected_failure(self, test, exception_str):
        """Write the expected failure to the stream.

        Args:
            test (TestCase): test item instance.
            exception_str (str): exception traceback string.
        """
        self.stream.writeln('Expected Failure: %s' % test, CYAN)
        self.write_details(exception_str, color=CYAN)

    def add_unexpected_success(self, test):
        """Write the test unexpected success to the stream.

        Args:
            test (TestCase): test item instance.
        """
        self.stream.writeln('Unexpected Success: %s' % test, BLUE)
