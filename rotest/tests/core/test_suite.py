"""Test TestSuite behavior and common variables."""
# pylint: disable=too-many-locals,protected-access
# pylint: disable=too-many-public-methods,invalid-name,old-style-class
# pylint: disable=no-member,protected-access,no-init,too-few-public-methods
import os

import django

from rotest import ROTEST_WORK_DIR
from rotest.core.suite import TestSuite
from rotest.common.colored_test_runner import colored_main
from rotest.management.models.ut_models import DemoResourceData
from rotest.tests.core.utils import (MockSuite1, MockSuite2, MockTestSuite,
                              MockNestedTestSuite, SuccessCase, FailureCase,
                              PartialCase, MockFlow, MockFlow1, MockFlow2,
                              SuccessBlock, FailureBlock, BasicRotestUnitTest)


class TestTestSuite(BasicRotestUnitTest):
    """Test TestSuite behavior on successful & failed components."""

    fixtures = ['case_ut.json']

    def test_empty_suite(self):
        """Test empty component tuple raises AttributeError."""
        MockTestSuite.components = ()
        self.assertRaises(AttributeError, MockTestSuite)

    def test_happy_flow(self):
        """Create test suite with success components & validate run success.

        We test the suite result was success and that all the components run.
        """
        MockSuite1.components = (SuccessCase, SuccessCase)
        MockSuite2.components = (SuccessCase,)

        MockTestSuite.components = (MockSuite1, MockSuite2)

        test_suite = MockTestSuite()
        self.run_test(test_suite)

        self.assertTrue(self.result.wasSuccessful(),
                        'Suite failed when it should have succeeded')

        self.assertEqual(self.result.testsRun, 3,
                         "Suite didn't run the correct number of tests")

        # === Validate data object ===
        self.assertTrue(test_suite.data.success,
                        'Suite data result should have been True')

        self.assertEquals(len(list(test_suite)),
                          len(MockTestSuite.components),
                          'Data members number differs form number of tests')

    def test_skip_init(self):
        """Create a suite that should skip initialization and validate it."""
        MockSuite1.components = (SuccessCase, SuccessCase)
        MockSuite2.components = (SuccessCase,)

        MockTestSuite.components = (MockSuite1, MockSuite2)

        test_suite = MockTestSuite(skip_init=True)
        self.run_test(test_suite)

        self.assertTrue(self.result.wasSuccessful(),
                        'Suite failed when it should have succeeded')

        self.assertEqual(self.result.testsRun, 3,
                         "Suite didn't run the correct number of tests")

        # === Validate data object ===
        self.assertTrue(test_suite.data.success,
                        'Suite data result should have been True')

        for resource_request in SuccessCase.resources:
            test_resource = DemoResourceData.objects.get(
                             ip_address=resource_request.kwargs['ip_address'])
            self.assertFalse(test_resource.initialization_flag,
                             "Resource %r was initialized" % test_resource)

    def test_suite_failure(self):
        """Create test suite with failed component & validate its behavior.

        We test the suite result was failure and all the component run.
        """
        MockSuite1.components = (SuccessCase, FailureCase)
        MockSuite2.components = (SuccessCase,)

        MockTestSuite.components = (MockSuite1, MockSuite2)

        test_suite = MockTestSuite()
        self.run_test(test_suite)

        self.assertFalse(self.result.wasSuccessful(),
                         'Suite succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 3,
                         "Suite didn't run the correct number of tests")

        self.assertEqual(len(self.result.failures), 1,
                         "Suite didn't fail the correct number of tests")

        # === Validate data object ===
        self.assertFalse(test_suite.data.success,
                         'Suite data result should have been False')

        self.assertEquals(len(list(test_suite)),
                          len(MockTestSuite.components),
                          'Number of components differs from the actual'
                          'number of tests')

    def test_case_method_failure(self):
        """Create test suite with failed method & validate the suite behavior.

        We test the suite result was failure and all the component run.
        """
        MockSuite1.components = (SuccessCase,)
        MockSuite2.components = (PartialCase,)

        MockTestSuite.components = (MockSuite1, MockSuite2)

        test_suite = MockTestSuite()
        self.run_test(test_suite)

        self.assertFalse(self.result.wasSuccessful(),
                         'Suite succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 3,
                         "Suite didn't run the correct number of tests")

        self.assertEqual(len(self.result.failures), 1,
                         "Suite didn't fail the correct number of tests")

    def test_nested_suite_happy_flow(self):
        """Create nested test suite and validate the test run success.

        We test the suite result was success and that all the components run.
        """
        MockSuite1.components = (SuccessCase, SuccessCase)
        MockSuite2.components = (SuccessCase,)

        MockNestedTestSuite.components = (MockSuite1, MockSuite2)

        MockTestSuite.components = (MockSuite1, MockNestedTestSuite)

        test_suite = MockTestSuite()
        self.run_test(test_suite)

        self.assertTrue(self.result.wasSuccessful(),
                        'Suite failed when it should have succeeded')

        self.assertEqual(self.result.testsRun, 5,
                         "Suite didn't run the correct number of tests")

        # === Validate data object ===
        self.assertTrue(test_suite.data.success,
                        'Suite data result should have been True')

        self.assertEquals(
            len(list(test_suite)),
            len(MockTestSuite.components),
            'Data members number differs form number of tests')

    def test_nested_suite_internal_fail(self):
        """Test nested test suite behavior on internal suite failure.

        We test the suite result was failure and that all the components run.
        """
        MockSuite1.components = (SuccessCase, FailureCase)
        MockSuite2.components = (SuccessCase,)

        MockNestedTestSuite.components = (MockSuite1, MockSuite2)

        MockTestSuite.components = (MockSuite2,
                                    MockNestedTestSuite,
                                    MockSuite2)

        test_suite = MockTestSuite()
        self.run_test(test_suite)

        self.assertFalse(self.result.wasSuccessful(),
                         'Suite succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 5,
                         "Suite didn't run the correct number of tests")

        self.assertEqual(len(self.result.failures), 1,
                         "Suite didn't fail the correct number of tests")

    def test_nested_suite_external_fail(self):
        """Test nested test suite behavior on external test failure.

        We test the suite result was failure and that all the components run.
        """
        MockSuite1.components = (SuccessCase,)
        MockSuite2.components = (FailureCase,)

        MockNestedTestSuite.components = (MockSuite1, MockSuite2)

        MockTestSuite.components = (MockSuite1,
                                    MockSuite2,
                                    MockNestedTestSuite,
                                    MockSuite2)

        test_suite = MockTestSuite()
        self.run_test(test_suite)

        self.assertFalse(self.result.wasSuccessful(),
                         'Suite succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 5,
                         "Suite didn't run the correct number of tests")

        self.assertEqual(len(self.result.failures), 3,
                         "Suite didn't fail the correct number of tests")

    def test_invalid_type(self):
        """Test invalid component type raises TypeError."""
        class BadTestType():
            pass

        MockSuite1.components = (SuccessCase,)
        MockTestSuite.components = (MockSuite1, BadTestType, MockSuite1)

        self.assertRaises(TypeError, MockTestSuite)

    def validate_work_dirs(self, test):
        """Validate the test work directories recursively.

        Validates that all tests working directories were created and that
        each sub test work directory is contained by its containing test work
        directory.

        Args:
            test (TestCase / TestSuite): test whose test data work dir
                is being validated.
        """
        self.assertTrue(os.path.exists(test.work_dir),
                        "Test %r work directory %r doesn't exists")

        sub_test_iterator = ()

        if isinstance(test, TestSuite):
            sub_test_iterator = iter(test)

        for sub_test in sub_test_iterator:
            base_work_dir = os.path.dirname(sub_test.work_dir)
            self.assertEqual(test.work_dir, base_work_dir, "Test %r "
                "work directory %r is not contained in its parent 's %r "
                "work directory %r" % (sub_test.data, sub_test.work_dir,
                                       test, test.work_dir))

    def test_suite_with_flow(self):
        """Create nested test suite and with test-flow validate success.

        We test the suite result was success and that all the components run.
        """
        MockFlow.blocks = (SuccessBlock, SuccessBlock)
        MockTestSuite.components = (SuccessCase, MockFlow, SuccessCase)

        test_suite = MockTestSuite()
        self.run_test(test_suite)

        self.assertTrue(self.result.wasSuccessful(),
                        'Suite failed when it should have succeeded')

        self.assertEqual(self.result.testsRun, 3,
                         "Suite didn't run the correct number of tests")

        # === Validate data object ===
        self.assertTrue(test_suite.data.success,
                        'Suite data result should have been True')

    def test_complex_nested_suite_with_flows(self):
        """Create nested test suite with test-flows and validate run success.

        We test the suite result was success and that all the components run.
        """
        MockFlow1.blocks = (SuccessBlock, SuccessBlock)
        MockFlow2.blocks = (FailureBlock, SuccessBlock)
        MockSuite1.components = (MockFlow2, SuccessCase)
        MockSuite2.components = (MockFlow1, MockFlow2)

        MockTestSuite.components = (MockSuite1, MockSuite2)

        test_suite = MockTestSuite()
        self.run_test(test_suite)

        self.assertFalse(self.result.wasSuccessful(),
                         'Suite succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 4,
                         "Suite didn't run the correct number of tests")

        self.assertEqual(len(self.result.failures), 2,
                         "Suite didn't fail the correct number of tests")

        # === Validate data object ===
        self.assertFalse(test_suite.data.success,
                         'Suite data result should have been False')

    def test_working_dir(self):
        """Test the tests working directories creation and structure.

        Validates that all tests working directories were created and each
        that sub test work directory is contained by its containing test work
        directory.

        It tests it using the following scenario:

            TestSuite
              - Suite1
              - Suite2
              - TestSuite
              -- Suite1
              -- Suite2
              - Suite2
        """
        MockSuite1.components = (SuccessCase,)
        MockSuite2.components = (FailureCase,)

        MockNestedTestSuite.components = (MockSuite1, MockSuite2)

        MockTestSuite.components = (MockSuite1,
                                    MockSuite2,
                                    MockNestedTestSuite,
                                    MockSuite2)

        test_suite = MockTestSuite()
        self.assertEqual(ROTEST_WORK_DIR.rstrip(os.path.sep),
             os.path.dirname(test_suite.work_dir).rstrip(os.path.sep),
             "Test %r work directory %r is not contained in the base work "
             "directory %r" %
             (test_suite.data, test_suite.work_dir, ROTEST_WORK_DIR))

        self.validate_work_dirs(test_suite)

if __name__ == '__main__':
    django.setup()
    colored_main(defaultTest='TestTestSuite')
