"""Remote database result handler."""
from __future__ import absolute_import

from rotest.core import TestCase
from rotest.core.models.case_data import TestOutcome
from rotest.management.client.result_client import ClientResultManager
from rotest.core.result.handlers.abstract_handler import AbstractResultHandler


class RemoteDBHandler(AbstractResultHandler):
    """Remote database result handler.

    Overrides result handler's methods to update a remote Rotest database
    values on each event change in the main result object.
    """
    NAME = 'remote'
    SKIP_DELTA_MESSAGE = "Previous run passed according to remote DB"

    SESSION_EXTRA_TIME = 3  # Seconds

    def __init__(self, *args, **kwargs):
        """Initialize the result handler and connect to the result server."""
        super(RemoteDBHandler, self).__init__(*args, **kwargs)
        self.client = ClientResultManager()
        self.client.connect()

    def start_test_run(self):
        """Save all the test datas and the run data in the remote db."""
        self.client.start_test_run(self.main_test)

    def stop_test_run(self):
        """Disconnect from the result server."""
        self.client.update_run_data(self.main_test.data.run_data)
        self.client.disconnect()

    def start_test(self, test):
        """Update the remote test data to 'in progress' and set the start time.

        Args:
            test (object): test item instance.
        """
        self.client.start_test(test)
        if isinstance(test, TestCase) or test.is_main:
            self.client.set_session_timeout(test.TIMEOUT +
                                            self.SESSION_EXTRA_TIME)

    def should_skip(self, test):
        """Check if the test passed in the last run according to the remote DB.

        The result is based on querying the results DB for the last run. If the
        last run was successful, then the test should be skipped.

        Args:
            test (object): test item instance.

        Returns:
            str. Skip reason if the test should be skipped, None otherwise.
        """
        if (test.data.run_data is not None and test.data.run_data.run_delta and
                self.client.should_skip(test)):

            return self.SKIP_DELTA_MESSAGE

        return None

    def update_resources(self, test):
        """Update the resources of the test in the remote db.

        Args:
            test (object): test item instance.
        """
        self.client.update_resources(test)

    def stop_test(self, test):
        """Finalize the remote test's data.

        Args:
            test (object): test item instance.
        """
        self.client.stop_test(test)

    def start_composite(self, test):
        """Update the remote test data to 'in progress' and set the start time.

        Args:
            test (rotest.core.suite.TestSuite): test item instance.
        """
        self.client.start_composite(test)

    def stop_composite(self, test):
        """Save the remote composite test's data.

        Args:
            test (rotest.core.suite.TestSuite): test item instance.
        """
        self.client.stop_composite(test)

    def add_success(self, test, msg):
        """Save the remote test data result as success.

        Args:
            test (object): test item instance.
            msg (str): success message.
        """
        self.client.add_result(test, TestOutcome.SUCCESS, msg)

    def add_skip(self, test, reason):
        """Save the remote test data result as skip.

        Args:
            test (object): test item instance.
            reason (str): skip reason description.
        """
        self.client.add_result(test, TestOutcome.SKIPPED, reason)

    def add_failure(self, test, exception_str):
        """Save the remote test data result as failure.

        Args:
            test (object): test item instance.
            exception_str (str): exception traceback string.
        """
        self.client.add_result(test, TestOutcome.FAILED,
                               exception_str)

    def add_error(self, test, exception_str):
        """Save the remote test data result as error.

        Args:
            test (object): test item instance.
            exception_str (str): exception traceback string.
        """
        self.client.add_result(test, TestOutcome.ERROR,
                               exception_str)

    def add_expected_failure(self, test, exception_str):
        """Save the remote test data result as expected failure.

        Args:
            test (object): test item instance.
            exception_str (str): exception traceback string.
        """
        self.client.add_result(test, TestOutcome.EXPECTED_FAILURE,
                               exception_str)

    def add_unexpected_success(self, test):
        """Save the remote test data result as unexpected success.

        Args:
            test (object): test item instance.
        """
        self.client.add_result(test, TestOutcome.UNEXPECTED_SUCCESS)
