""""Stream dots layout result handler."""
# pylint: disable=invalid-name,too-few-public-methods,arguments-differ
# pylint: disable=too-many-arguments,super-init-not-called,unused-argument
from base_handler import BaseStreamHandler
from rotest.common.constants import GREEN, YELLOW, RED, BOLD, CYAN, BLUE


class DotsHandler(BaseStreamHandler):
    """Stream dots layout result handler.

    Overrides result handler's methods to print each event change in
    the main result object in dots layout to the given stream.
    """
    NAME = 'dots'

    def add_success(self, test):
        """Write the test success to the stream.

        Args:
            test (rotest.core.case.TestCase): test item instance.
        """
        self.stream.write('.', GREEN)

    def add_skip(self, test, reason):
        """Write the test skip to the stream.

        Args:
            test (rotest.core.case.TestCase): test item instance.
            reason (str): skip reason description.
        """
        self.stream.write('s', YELLOW)

    def add_failure(self, test, exception_str):
        """Write the failure to the stream.

        Args:
            test (rotest.core.case.TestCase): test item instance.
            exception_str (str): exception traceback string.
        """
        self.stream.write('F', RED)

    def add_error(self, test, exception_str):
        """Write the failure to the stream.

        Args:
            test (rotest.core.case.TestCase): test item instance.
            exception_str (str): exception traceback string.
        """
        self.stream.write('E', RED, BOLD)

    def add_expected_failure(self, test, exception_str):
        """Write the expected failure to the stream.

        Args:
            test (rotest.core.case.TestCase): test item instance.
            exception_str (str): exception traceback string.
        """
        self.stream.write('x', CYAN)

    def add_unexpected_success(self, test):
        """Write the test unexpected success to the stream.

        Args:
            test (rotest.core.case.TestCase): test item instance.
        """
        self.stream.write('u', BLUE)
