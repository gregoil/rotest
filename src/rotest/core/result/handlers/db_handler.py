"""Database result handler."""
# pylint: disable=unused-argument
from .abstract_handler import AbstractResultHandler


class DBHandler(AbstractResultHandler):
    """Database result handler.

    Overrides result handler's methods to update the Rotest's database
    values on each event change in the main result object.
    """
    NAME = 'db'

    SKIP_DELTA_MESSAGE = "Previous run passed according to local DB"

    @staticmethod
    def _save_resource(resource, test):
        """Save a copy of the resource to the DB and link it to the Case.

        Args:
            resource (BaseResource): a resource to save.
        """
        if resource.DATA_CLASS is None:
            return

        test.logger.debug("Saving a copy of resource %r", resource.name)

        copy_resource = resource.data.duplicate()
        test.data.resources.add(copy_resource)
        test.logger.debug("Resource %r duplicated with name %r",
                          resource.name, copy_resource.name)

    @classmethod
    def _save_sub_tests(cls, test, run_data):
        """Assign the tests' datas with the saved run data and save them.

        Args:
            test (object): test item instance.
            run_data (rotest.core.models.run_data.RunData): test run data.
        """
        test.data.run_data = run_data
        test.data.save()

        if test.IS_COMPLEX:
            for sub_test in test:
                test.data.add_sub_test_data(sub_test.data)
                cls._save_sub_tests(sub_test, run_data)

    def start_test_run(self):
        """Save all the test datas and the run data."""
        if self.main_test is None:
            return

        run_data = self.main_test.data.run_data
        if run_data is not None:
            # Save the run data so it'll have a pk.
            run_data.save()

        # Save all the test datas so they'll have a pk.
        self._save_sub_tests(self.main_test, run_data)

        if run_data is not None:
            # Repoint to the main test, now that it has a pk.
            run_data.main_test = self.main_test.data
            run_data.save()

    def start_test(self, test):
        """Update the test data to 'in progress' state and set the start time.

        Args:
            test (object): test item instance.
        """
        test.data.save()

    def should_skip(self, test):
        """Check if the test passed in the last run.

        The result is based on querying the local DB for the last run. If the
        last run was successful, then the test should be skipped.

        Args:
            test (object): test item instance.

        Returns:
            str. Skip reason if the test should be skipped, None otherwise.
        """
        if (test.data.run_data is not None and
                test.data.run_data.run_delta and
                test.data.should_skip(test.data.name, test.data.run_data,
                                      test.data.pk)):
            return self.SKIP_DELTA_MESSAGE

        return None

    def update_resources(self, test):
        """Save a copy of the test's resources and point to them in the db.

        Args:
            test (object): test item instance.
        """
        test.data.resources.clear()
        if test.locked_resources is not None:
            for resource in test.locked_resources.itervalues():
                self._save_resource(resource, test)

    def stop_test(self, test):
        """Finalize the test's data and save a copy of its resources.

        Args:
            test (object): test item instance.
        """
        test.data.save()

    def start_composite(self, test):
        """Update the test data to 'in progress' state and set the start time.

        Args:
            test (TestSuite): test item instance.
        """
        self.start_test(test)

    def stop_composite(self, test):
        """Save the composite test's data.

        Args:
            test (TestSuite): test item instance.
        """
        test.data.save()

    def add_success(self, test):
        """Save the test data result as success.

        Args:
            test (object): test item instance.
        """
        test.data.save()

    def add_skip(self, test, reason):
        """Save the test data result as skip.

        Args:
            test (object): test item instance.
            reason (str): skip reason description.
        """
        test.data.save()

    def add_failure(self, test, exception_str):
        """Save the test data result as failure.

        Args:
            test (object): test item instance.
            exception_str (str): exception traceback string.
        """
        test.data.save()

    def add_error(self, test, exception_str):
        """Save the test data result as error.

        Args:
            test (object): test item instance.
            exception_str (str): exception traceback string.
        """
        test.data.save()

    def add_expected_failure(self, test, exception_str):
        """Save the test data result as expected failure.

        Args:
            test (object): test item instance.
            exception_str (str): exception traceback string.
        """
        test.data.save()

    def add_unexpected_success(self, test):
        """Save the test data result as unexpected success.

        Args:
            test (object): test item instance.
        """
        test.data.save()
