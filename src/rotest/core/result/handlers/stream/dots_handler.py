""""Stream dots layout result handler."""
# pylint: disable=invalid-name,too-few-public-methods,arguments-differ
# pylint: disable=too-many-arguments,super-init-not-called,unused-argument
from functools import wraps

from base_handler import BaseStreamHandler
from rotest.core.flow_component import AbstractFlowComponent
from rotest.common.constants import GREEN, YELLOW, RED, BOLD, CYAN, BLUE


def check_main_decorator(func):
    """Only call the handler method on test cases and top test flows.

    Args:
        func (function): handler method to decorate.

    Returns:
        function. wrapped method that only runs on main tests.
    """
    @wraps(func)
    def check_main(self, test, *args, **kwargs):
        if not isinstance(test, AbstractFlowComponent) or test.is_main:
            return func(self, test, *args, **kwargs)

    return check_main


class DotsHandler(BaseStreamHandler):
    """Stream dots layout result handler.

    Overrides result handler's methods to print each event change in
    the main result object in dots layout to the given stream.
    """
    NAME = 'dots'

    @check_main_decorator
    def add_success(self, test):
        """Write the test success to the stream.

        Args:
            test (rotest.core.case.TestCase): test item instance.
        """
        self.stream.write('.', GREEN)

    @check_main_decorator
    def add_skip(self, test, reason):
        """Write the test skip to the stream.

        Args:
            test (rotest.core.case.TestCase): test item instance.
            reason (str): skip reason description.
        """
        self.stream.write('s', YELLOW)

    @check_main_decorator
    def add_failure(self, test, exception_str):
        """Write the failure to the stream.

        Args:
            test (rotest.core.case.TestCase): test item instance.
            exception_str (str): exception traceback string.
        """
        self.stream.write('F', RED)

    @check_main_decorator
    def add_error(self, test, exception_str):
        """Write the failure to the stream.

        Args:
            test (rotest.core.case.TestCase): test item instance.
            exception_str (str): exception traceback string.
        """
        self.stream.write('E', RED, BOLD)

    @check_main_decorator
    def add_expected_failure(self, test, exception_str):
        """Write the expected failure to the stream.

        Args:
            test (rotest.core.case.TestCase): test item instance.
            exception_str (str): exception traceback string.
        """
        self.stream.write('x', CYAN)

    @check_main_decorator
    def add_unexpected_success(self, test):
        """Write the test unexpected success to the stream.

        Args:
            test (rotest.core.case.TestCase): test item instance.
        """
        self.stream.write('u', BLUE)
