"""Tests for the result client-server mechanism."""
# pylint: disable=invalid-name,too-many-public-methods,protected-access
import django

from rotest.core.models import GeneralData
from rotest.core.models.run_data import RunData
from rotest.management.common.utils import LOCALHOST
from rotest.common.colored_test_runner import colored_main
from rotest.common.django_utils.common import get_sub_model
from rotest.core.models.case_data import TestOutcome, CaseData
from rotest.management.client.result_client import ClientResultManager
from rotest.management.models.ut_models import DemoResource, DemoResourceData
from rotest.tests.management.resource_base_test import \
                                                 BaseResourceManagementTest
from rotest.tests.core.utils import (MockTestSuite, MockSuite1, MockSuite2,
                                     MockCase, MockCase1, MockCase2,
                                     SuccessCase)


class TestResultManagement(BaseResourceManagementTest):
    """Result management tests."""
    fixtures = ['resource_ut.json']

    def setUp(self):
        """Initialize and connect a client to the server."""
        super(TestResultManagement, self).setUp()

        self.client = ClientResultManager(LOCALHOST)
        self.client.connect()

    def tearDown(self):
        """Disconnect the client from the server."""
        self.client.disconnect()

        super(TestResultManagement, self).tearDown()

    def _validate_tests_tree(self, main_test):
        """Validate that the tests' data in the DB is as expected.

        Args:
            main_test (TestCase / TestCase / TestSuite): main test of the run.

        Returns:
            GeneralData. the test's data as appears in the DB.
        """
        try:
            db_clone = GeneralData.objects.get(name=main_test.data.name)

        except GeneralData.DoesNotExist:
            self.fail("DB instance of %r wasn't created" % main_test.data.name)

        self.assertEqual(db_clone.success, main_test.data.success)
        self.assertEqual(db_clone.status, main_test.data.status)
        if main_test.IS_COMPLEX:
            for sub_test in main_test:
                sub_data = self._validate_tests_tree(sub_test)
                data_leaf = get_sub_model(sub_data)
                sub_test_parent = data_leaf.parent
                self.assertIsNotNone(sub_test_parent,
                                     "%r's data is not connected to a parent" %
                                     sub_test.data.name)
                self.assertEqual(sub_test_parent.name, main_test.data.name,
                                 "%r's data is not connected to the right"
                                 "parent (%r instead of %r)" %
                                 (sub_test.data.name,
                                  sub_test_parent.name,
                                  main_test.data.name))

        return db_clone

    def _validate_has_times(self, test_item, start_time=False, end_time=False):
        """Validate that the test's start and end time is as expected.

        Args:
            test_item (TestCase / TestCase / TestSuite): test to validate.
            start_time (bool): is start time expected to be set.
            end_time (bool): is end time expected to be set.
        """
        test_data = GeneralData.objects.get(name=test_item.data.name)

        self.assertEqual(test_data.start_time is not None, start_time,
                         "Unexpected start time value for %r "
                         "(expected to be set = %s, actual value = %r)" %
                         (test_data.name, start_time, test_data.start_time))

        self.assertEqual(test_data.end_time is not None, end_time,
                         "Unexpected end time value for %r "
                         "(expected to be set = %s, actual value = %r)" %
                         (test_data.name, end_time, test_data.end_time))

    def _validate_test_result(self, test_item, success=None, error_tuple=None):
        """Validate the test's success and error description values.

        Args:
            test_item (TestCase / TestCase / TestSuite): test to validate.
            success (bool): is start time expected to be set.
            error_tuple (tuple): values to test exception type and string,
                leave None to not validate those values.
        """
        test_data = GeneralData.objects.get(name=test_item.data.name)

        self.assertEqual(test_data.success, success,
                         "Unexpected success value for %r "
                         "(got %r, expected %r)" %
                         (test_data.name, test_data.success, success))

        if error_tuple is not None:
            test_data = test_data.casedata
            actual_error_value = (test_data.exception_type,
                                  test_data.traceback)
            self.assertEqual(actual_error_value, error_tuple,
                             "Unexpected error value for %r "
                             "(got %r, expected %r)" %
                             (test_data.name, actual_error_value, error_tuple))

    def test_tree_building(self):
        """Test that the manager can build the tests' tree properly."""
        MockSuite1.components = (MockSuite2, MockTestSuite)
        MockSuite2.components = (MockCase, MockCase1, MockCase2)
        MockTestSuite.components = (SuccessCase,)

        run_data = RunData(run_name='test_run_name')
        main_test = MockSuite1(run_data=run_data)

        self.client.start_test_run(main_test)

        self._validate_tests_tree(main_test)

        try:
            db_run_data = RunData.objects.get()

        except RunData.DoesNotExist:
            self.fail("DB instance of the run data wasn't created")

        self.assertEqual(db_run_data.run_name, run_data.run_name)

    def test_start_test(self):
        """Test that the start_test method starts the test's data."""
        MockTestSuite.components = (SuccessCase,)

        run_data = RunData(run_name=None)
        main_test = MockTestSuite(run_data=run_data)
        test_case = next(iter(main_test))

        self.client.start_test_run(main_test)
        self._validate_has_times(test_case, start_time=False)

        self.client.start_test(test_case)
        self._validate_has_times(test_case, start_time=True)

    def test_stop_test(self):
        """Test that the stop_test method ends the test's data."""
        MockTestSuite.components = (SuccessCase,)

        run_data = RunData(run_name=None)
        main_test = MockTestSuite(run_data=run_data)
        test_case = next(iter(main_test))

        self.client.start_test_run(main_test)
        self._validate_has_times(test_case, start_time=False, end_time=False)

        self.client.start_test(test_case)
        self._validate_has_times(test_case, start_time=True, end_time=False)

        self.client.stop_test(test_case)
        self._validate_has_times(test_case, start_time=True, end_time=False)

    def test_update_resources(self):
        """Test that the update_resources method updates the test's data."""
        MockTestSuite.components = (SuccessCase,)

        run_data = RunData(run_name=None)
        main_test = MockTestSuite(run_data=run_data)
        test_case = next(iter(main_test))

        test_case.locked_resources = {'test_resource': DemoResource(
                  DemoResourceData.objects.get(name='available_resource1'))}

        self.client.start_test_run(main_test)
        self.client.start_test(test_case)
        self.client.update_resources(test_case)

        test_data = CaseData.objects.get(name=test_case.data.name)

        self.assertEqual(test_data.resources.count(),
                         len(test_case.locked_resources),
                         "Wrong resources count, (expected resources %r, "
                         "actual resources %r)" %
                         (test_case.locked_resources.values(),
                          test_data.resources.all()))

        for resource in test_case.locked_resources.itervalues():
            self.assertEqual(
                     test_data.resources.filter(name=resource.name).count(), 1,
                     "Resource %r wasn't found in %r" %
                     (resource.name, test_data.resources.all()))

    def test_start_composite(self):
        """Test that the start_composite method starts the test's data."""
        MockTestSuite.components = (SuccessCase,)

        run_data = RunData(run_name=None)
        main_test = MockTestSuite(run_data=run_data)

        self.client.start_test_run(main_test)
        self._validate_has_times(main_test, start_time=False)

        self.client.start_composite(main_test)
        self._validate_has_times(main_test, start_time=True)

    def test_stop_composite(self):
        """Test that the stop_composite method ends the test's data."""
        MockTestSuite.components = (SuccessCase,)

        run_data = RunData(run_name=None)
        main_test = MockTestSuite(run_data=run_data)

        self.client.start_test_run(main_test)
        self._validate_has_times(main_test, start_time=False, end_time=False)

        self.client.start_composite(main_test)
        self._validate_has_times(main_test, start_time=True, end_time=False)

        self.client.stop_composite(main_test)
        self._validate_has_times(main_test, start_time=True, end_time=True)

    def test_add_result(self):
        """Test that the add_result method updates the test's data.

        This test simulates the workflow of running a test in server side:
        * Start a case and a case.
        * Assert that the result values are not yet set.
        * Stop the test and add a result.
        * Assert that the case's and case's results are as expected.
        """
        MockTestSuite.components = (SuccessCase,)

        run_data = RunData(run_name=None)
        main_test = MockTestSuite(run_data=run_data)
        test_case = next(iter(main_test))

        # Simulate starting the test.
        self.client.start_test_run(main_test)
        self.client.start_composite(main_test)
        self.client.start_test(test_case)

        # Check that the results are still None.
        self._validate_test_result(main_test, success=None)
        self._validate_test_result(test_case, success=None,
                                   error_tuple=(None, ''))

        # Simulate ending the test.
        self.client.stop_test(test_case)
        ERROR_STRING = 'test error'
        self.client.add_result(test_case, TestOutcome.ERROR, ERROR_STRING)
        self.client.stop_composite(main_test)

        # Check that the results are updated.
        self._validate_test_result(test_case, success=False,
                               error_tuple=(TestOutcome.ERROR, ERROR_STRING))
        self._validate_test_result(main_test, success=False)


if __name__ == '__main__':
    django.setup()
    colored_main(defaultTest='TestResultManagement')
