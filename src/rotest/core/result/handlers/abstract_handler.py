"""Abstract result handler."""
# pylint: disable=invalid-name,too-few-public-methods,arguments-differ
# pylint: disable=too-many-arguments,unused-argument,no-self-use
from abc import ABCMeta


class AbstractResultHandler(object):
    """Result handler interface.

    Defines the required interface for all the result handlers.

    Attributes:
        main_test (rotest.core.abstract_test.AbstractTest): the main test
            instance (e.g. TestSuite instance or TestFlow instance).
    """
    __metaclass__ = ABCMeta

    NAME = NotImplemented

    def __init__(self, main_test=None, *args, **kwargs):
        self.main_test = main_test

    def start_test_run(self):
        """Called once before any tests are executed."""
        pass

    def start_test(self, test):
        """Called when the given test is about to be run.

        Args:
            test (rotest.core.abstract_test.AbstractTest): test item instance.
        """
        pass

    def should_skip(self, test):
        """Check if the test should be skipped.

        Args:
            test (rotest.core.abstract_test.AbstractTest): test item instance.

        Returns:
            str: skip reason if the test should be skipped, None otherwise.
        """
        return None

    def update_resources(self, test):
        """Called once after locking the tests resources.

        Args:
            test (rotest.core.abstract_test.AbstractTest): test item instance.
        """
        pass

    def setup_finished(self, test):
        """Called when the given test finished setting up.

        Args:
            test (rotest.core.abstract_test.AbstractTest): test item instance.
        """
        pass

    def start_teardown(self, test):
        """Called when the given test is starting its teardown.

        Args:
            test (rotest.core.abstract_test.AbstractTest): test item instance.
        """
        pass

    def stop_test(self, test):
        """Called when the given test has been run.

        Args:
            test (rotest.core.abstract_test.AbstractTest): test item instance.
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
        """Called when a test has completed successfully.

        Args:
            test (rotest.core.abstract_test.AbstractTest): test item instance.
        """
        pass

    def add_skip(self, test, reason):
        """Called when a test is skipped.

        Args:
            test (rotest.core.abstract_test.AbstractTest): test item instance.
            reason (str): reason for skipping the test.
        """
        pass

    def add_failure(self, test, exception_string):
        """Called when an error has occurred.

        Args:
            test (rotest.core.abstract_test.AbstractTest): test item instance.
            exception_string (str): exception description.
        """
        pass

    def add_error(self, test, exception_string):
        """Called when an error has occurred.

        Args:
            test (rotest.core.abstract_test.AbstractTest): test item instance.
            exception_string (str): exception description.
        """
        pass

    def add_expected_failure(self, test, exception_string):
        """Called when an expected failure/error occurred.

        Args:
            test (rotest.core.abstract_test.AbstractTest): test item instance.
            exception_string (str): exception description.
        """
        pass

    def add_unexpected_success(self, test):
        """Called when a test was expected to fail, but succeed.

        Args:
            test (rotest.core.abstract_test.AbstractTest): test item instance.
        """
        pass

    def print_errors(self, tests_run, errors, skipped, failures,
                     expected_failures, unexpected_successes):
        """Called by TestRunner after test run.

        Args:
            tests_run (number): count of tests that has been run.
            errors (list): error tests details list.
            skipped (list): skipped tests details list.
            failures (list): failed tests details list.
            expected_failures (list): expected-to-fail tests details list.
            unexpected_successes (list): unexpected successes tests details
                list.
        """
        pass
