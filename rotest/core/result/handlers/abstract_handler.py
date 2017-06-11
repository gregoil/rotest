"""Abstract result handler."""
# pylint: disable=invalid-name,too-few-public-methods,arguments-differ
# pylint: disable=too-many-arguments,unused-argument,no-self-use
from abc import ABCMeta


class AbstractResultHandler(object):
    """Result handler interface.

    Defines the required interface for all the result handlers.

    Attributes:
        main_test (object): the main test instance (e.g. TestSuite instance
            or TestFlow instance).
    """
    __metaclass__ = ABCMeta

    NAME = NotImplemented

    def __init__(self, main_test=None, *args, **kwargs):
        """Initialize the result handler.

        Args:
            main_test (object): the main test instance (e.g. TestSuite instance
                or TestFlow instance).
        """
        self.main_test = main_test

    def start_test_run(self):
        """Called once before any tests are executed."""
        pass

    def start_test(self, test):
        """Called when the given test is about to be run.

        Args:
            test (object): test item instance.
        """
        pass

    def should_skip(self, test):
        """Check if the test should be skipped.

        Note:
            Override to implement a 'should_skip' check.

        Args:
            test (object): test item instance.

        Returns:
            str. skip reason if the test should be skipped, None otherwise.
        """
        return None

    def update_resources(self, test):
        """Called once after locking the tests resources.

        Args:
            test (object): test item instance.
        """
        pass

    def stop_test(self, test):
        """Called when the given test has been run.

        Args:
            test (object): test item instance.
        """
        pass

    def start_composite(self, test):
        """Called when the given TestSuite is about to be run.

        Args:
            test (rotest.core.suite.TestSuite): test item instance.
        """
        pass

    def stop_composite(self, test):
        """Called when the given TestSuite has been run.

        Args:
            test (rotest.core.suite.TestSuite): test item instance.
        """
        pass

    def stop_test_run(self):
        """Called once after all tests are executed."""
        pass

    def add_success(self, test):
        """Called when a test has completed successfully."""
        pass

    def add_skip(self, test, reason):
        """Called when a test is skipped."""
        pass

    def add_failure(self, test, exception_string):
        """Called when an error has occurred."""
        pass

    def add_error(self, test, exception_string):
        """Called when an error has occurred."""
        pass

    def add_expected_failure(self, test, exception_string):
        """Called when an expected failure/error occurred."""
        pass

    def add_unexpected_success(self, test):
        """Called when a test was expected to fail, but succeed."""
        pass

    def print_errors(self, tests_run, errors, skipped, failures,
                     expected_failures, unexpected_successes):
        """Called by TestRunner after test run."""
        pass
