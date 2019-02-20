""""Stream dots layout result handler."""
# pylint: disable=invalid-name,too-few-public-methods,arguments-differ
# pylint: disable=too-many-arguments,super-init-not-called,unused-argument
from __future__ import absolute_import
from functools import wraps

from rotest.core.flow_component import AbstractFlowComponent
from rotest.common.constants import GREEN, YELLOW, RED, BOLD, CYAN, BLUE
from rotest.core.result.handlers.stream.base_handler import BaseStreamHandler


def ignore_subtests(func):
    """Only call the handler method on test cases and top test flows.

    Args:
        func (function): handler method to decorate.

    Returns:
        function. wrapped method that only runs on main tests.
    """
    @wraps(func)
    def ignore_subtests_wrapper(self, test, *args, **kwargs):
        if not isinstance(test, AbstractFlowComponent) or test.is_main:
            return func(self, test, *args, **kwargs)

    return ignore_subtests_wrapper


class DotsHandler(BaseStreamHandler):
    """Stream dots layout result handler.

    Overrides result handler's methods to print each event change in
    the main result object in dots layout to the given stream.
    """
    NAME = 'dots'

    @ignore_subtests
    def add_success(self, test, msg):
        """Write the test success to the stream.

        Args:
            test (rotest.core.case.TestCase): test item instance.
            msg (str): success message.
        """
        self.stream.write('.', GREEN)

    @ignore_subtests
    def add_skip(self, test, reason):
        """Write the test skip to the stream.

        Args:
            test (rotest.core.case.TestCase): test item instance.
            reason (str): skip reason description.
        """
        self.stream.write('s', YELLOW)

    @ignore_subtests
    def add_failure(self, test, exception_str):
        """Write the failure to the stream.

        Args:
            test (rotest.core.case.TestCase): test item instance.
            exception_str (str): exception traceback string.
        """
        self.stream.write('F', RED)

    @ignore_subtests
    def add_error(self, test, exception_str):
        """Write the failure to the stream.

        Args:
            test (rotest.core.case.TestCase): test item instance.
            exception_str (str): exception traceback string.
        """
        self.stream.write('E', RED, BOLD)

    @ignore_subtests
    def add_expected_failure(self, test, exception_str):
        """Write the expected failure to the stream.

        Args:
            test (rotest.core.case.TestCase): test item instance.
            exception_str (str): exception traceback string.
        """
        self.stream.write('x', CYAN)

    @ignore_subtests
    def add_unexpected_success(self, test):
        """Write the test unexpected success to the stream.

        Args:
            test (rotest.core.case.TestCase): test item instance.
        """
        self.stream.write('u', BLUE)
