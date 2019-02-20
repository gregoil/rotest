"""Tree format stream output handler."""
# pylint: disable=invalid-name,too-few-public-methods,arguments-differ
# pylint: disable=too-many-arguments,super-init-not-called,unused-argument
from __future__ import absolute_import
from rotest.common.constants import GREEN, YELLOW, RED, BOLD, CYAN, BLUE
from rotest.core.result.handlers.stream.base_handler import \
                                                BaseStreamHandler, NEW_LINE


class TreeHandler(BaseStreamHandler):
    """Stream tree layout result handler.

    Overrides result handler's methods to print each event change in
    the main result object in a tree layout to the given stream.
    """
    NAME = 'tree'

    def get_description(self, test):
        """Get the test's description including indentation and parents.

        Args:
            test (rotest.core.case.TestCase): the current test.

        Returns:
            str. test's description including indentation and parents.
        """
        indentation = test.parents_count * self.INDENTATION
        if not test.IS_COMPLEX:
            return indentation + test.data.name + ' ... '

        return indentation + test.data.name

    def start_test(self, test):
        """Write the test start to the stream.

        Args:
            test (TestSuite / TestCase): test item instance.
        """
        self.stream.write(NEW_LINE + self.get_description(test))

    def start_composite(self, test):
        """Called when the given TestSuite or TestCase is about to be run.

        Args:
            test (TestSuite): test item instance.
        """
        self.start_test(test)

    def add_success(self, test, msg):
        """Write the test success to the stream.

        Args:
            test (TestCase): test item instance.
            msg (str): success message.
        """
        if test.IS_COMPLEX:
            indentation = test.parents_count * self.INDENTATION
            self.stream.write(NEW_LINE + indentation)

        self.stream.write('OK ', GREEN)

    def add_skip(self, test, reason):
        """Write the test skip to the stream.

        Args:
            test (TestCase): test item instance.
            reason (str): skip reason description.
        """
        if test.IS_COMPLEX:
            indentation = test.parents_count * self.INDENTATION
            self.stream.write(NEW_LINE + indentation)

        self.stream.write('SKIP ', YELLOW)

    def add_failure(self, test, exception_str):
        """Write the failure to the stream.

        Args:
            test (TestCase): test item instance.
            exception_str (str): exception traceback string.
        """
        if test.IS_COMPLEX:
            indentation = test.parents_count * self.INDENTATION
            self.stream.write(NEW_LINE + indentation)

        self.stream.write('FAIL ', RED)

    def add_error(self, test, exception_str):
        """Write the failure to the stream.

        Args:
            test (TestCase): test item instance.
            exception_str (str): exception traceback string.
        """
        if test.IS_COMPLEX:
            indentation = test.parents_count * self.INDENTATION
            self.stream.write(NEW_LINE + indentation)

        self.stream.write('ERROR ', RED, BOLD)

    def add_expected_failure(self, test, exception_str):
        """Write the expected failure to the stream.

        Args:
            test (TestCase): test item instance.
            exception_str (str): exception traceback string.
        """
        if test.IS_COMPLEX:
            indentation = test.parents_count * self.INDENTATION
            self.stream.write(NEW_LINE + indentation)

        self.stream.write('ExpectedFailure ', CYAN)

    def add_unexpected_success(self, test):
        """Write the test unexpected success to the stream.

        Args:
            test (TestCase): test item instance.
        """
        if test.IS_COMPLEX:
            indentation = test.parents_count * self.INDENTATION
            self.stream.write(NEW_LINE + indentation)

        self.stream.write('UnexpectedSuccess ', BLUE)
