"""Test Rotest's TestCase class behavior."""
# pylint: disable=missing-docstring,unused-argument,protected-access
# pylint: disable=no-member,no-self-use,too-many-public-methods,invalid-name
import os
import re
import django

from rotest.core.case import request
from rotest.tests.core.utils import BasicRotestUnitTest
from rotest.common.colored_test_runner import colored_main
from rotest.core.models.case_data import TestOutcome, CaseData
from rotest.management.client.manager import ClientResourceManager
from rotest.management.models.ut_models import (DemoResource,
                                                DemoResourceData,
                                                NonExistingResource)
from utils import (ErrorInSetupCase, SuccessCase, FailureCase, ErrorCase,
                   StoreMultipleFailuresCase, UnexpectedSuccessCase,
                   DynamicResourceLockingCase, StoreFailureErrorCase,
                   ExpectedFailureCase, StoreFailureCase, MockTestSuite)


RESOURCE_NAME = 'available_resource1'


class TempSuccessCase(SuccessCase):
    """Inherit class and override resources requests."""
    resources = (request('test_resource', DemoResource,
                         name=RESOURCE_NAME, dirty=False,),)


class TempDynamicResourceLockingCase(DynamicResourceLockingCase):
    """Inherit class and override resources requests."""
    resources = (request('test_resource', DemoResource,
                         name=RESOURCE_NAME, dirty=False,),)


class TempFailureCase(FailureCase):
    """Inherit class and override resources requests."""
    resources = (request('test_resource', DemoResource,
                         name=RESOURCE_NAME, dirty=False,),)


class TempStoreFailureCase(StoreFailureCase):
    """Inherit class and override resources requests."""
    resources = (request('test_resource', DemoResource,
                         name=RESOURCE_NAME, dirty=False,),)


class TempErrorCase(ErrorCase):
    """Inherit class and override resources requests."""
    resources = (request('test_resource', DemoResource,
                         name=RESOURCE_NAME, dirty=False,),)


class TempStoreFailureErrorCase(StoreFailureErrorCase):
    """Inherit class and override resources requests."""
    resources = (request('test_resource', DemoResource,
                         name=RESOURCE_NAME, dirty=False,),)


class TempErrorInSetupCase(ErrorInSetupCase):
    """Inherit class and override resources requests."""
    resources = (request('test_resource', DemoResource,
                         name=RESOURCE_NAME, dirty=False,),)


class TempExpectedFailureCase(ExpectedFailureCase):
    """Inherit class and override resources requests."""
    resources = (request('test_resource', DemoResource,
                         name=RESOURCE_NAME, dirty=False,),)


class TempUnexpectedSuccessCase(UnexpectedSuccessCase):
    """Inherit class and override resources requests."""
    resources = (request('test_resource', DemoResource,
                         name=RESOURCE_NAME, dirty=False,),)


class TempStoreMultipleFailuresCase(StoreMultipleFailuresCase):
    """Inherit class and override resources requests."""
    resources = (request('test_resource', DemoResource,
                         name=RESOURCE_NAME, dirty=False,),)


class TestTestCase(BasicRotestUnitTest):
    """Test TestCase in different scenarios.

    Attributes:
        result (unittest.TestResult): used in tests as run result object.
    """
    fixtures = ['resource_ut.json']

    LOCK_TIMEOUT = 4
    FAKE_OWNER = 'owner'
    DEMO_RESOURCE_NAME = 'test_resource'

    def setUp(self):
        """Initialize and connect a client to resource manager.

        Create the basic fixture for the following tests.
        """
        super(TestTestCase, self).setUp()

        self.version = 1
        self.ip_address = '1.1.1.1'

    def _run_case(self, test_case):
        """Run given case and return it.

        Args:
            test_case (rotest.core.case.TestCase): case to run.

        Returns:
            rotest.core.case.TestCase. the case.
        """
        class InternalSuite(MockTestSuite):
            components = (test_case,)

        test_suite = InternalSuite()
        self.run_test(test_suite)
        return next(iter(test_suite))

    def test_success_case_run(self):
        """Test a TestCase on successful run.

        * Defines the registered resource as required resource.
        * Runs the test under a test suite.
        * Validates the result.
        * Validates the case's data object.
        * Validates the resource's state.
        """
        TempSuccessCase.resources = (request('test_resource',
                                          DemoResource,
                                          name=RESOURCE_NAME,
                                          dirty=False,),)

        case = self._run_case(TempSuccessCase)

        self.assertTrue(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        # === Validate case data object ===
        self.assertTrue(case.data.success)

        test_resource = case.locked_resources[self.DEMO_RESOURCE_NAME]
        self.assertTrue(isinstance(test_resource, DemoResource),
                "State resource data type should have been 'DemoResourceData'")

        self.assertEqual(case.data.exception_type, TestOutcome.SUCCESS,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.SUCCESS, case.data.exception_type))

        self.assertEqual(test_resource.mode,
                         DemoResourceData.BOOT_MODE,
                         "State resource mode attribute should "
                         "have been 'boot'")

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.validate_resource(test_resource, dirty=False)

    def test_dynamic_resources_locking(self):
        """Test that cases can dynamically lock resources.

        * Run a test that dynamically requests resources.
        * Validate that the resources were initialized and finalized.
        """
        TempDynamicResourceLockingCase.resources = (request('test_resource',
                                                         DemoResource,
                                                         name=RESOURCE_NAME,
                                                         dirty=False,),)
        dynamic_resource_name = 'available_resource2'
        TempDynamicResourceLockingCase.dynamic_resources = (
                                                 request('dynamic_resource',
                                                 DemoResource,
                                                 name=dynamic_resource_name,
                                                 dirty=False,),)

        case = self._run_case(TempDynamicResourceLockingCase)

        self.assertTrue(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        # === Validate case data object ===
        self.assertTrue(case.data.success)

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)
        self.validate_resource(test_resource, dirty=False)
        test_resource = DemoResourceData.objects.get(
                                                 name=dynamic_resource_name)
        self.validate_resource(test_resource, dirty=False)

    def test_failed_case_run(self):
        """Test a TestCase on run failure.

        * Defines the registered resource as required resource.
        * Runs the test under a test suite.
        * Validates that the test failed.
        * Validates the case's data object.
        * Validates the resource's state.
        """
        TempFailureCase.resources = (request('test_resource',
                                          DemoResource,
                                          name=RESOURCE_NAME,
                                          dirty=False,),)

        case = self._run_case(TempFailureCase)

        self.assertFalse(self.result.wasSuccessful(),
                         'Case succeeded when it should have failed')

        # === Validate case data object ===
        self.assertFalse(case.data.success,
                         'Case data result should have been False')

        self.assertEqual(case.data.exception_type, TestOutcome.FAILED,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.FAILED, case.data.exception_type))

        test_resource = case.locked_resources[self.DEMO_RESOURCE_NAME]

        self.assertTrue(isinstance(test_resource, DemoResource),
                "State resource type should have been 'DemoResource'")

        self.assertEqual(test_resource.mode,
                         DemoResourceData.BOOT_MODE,
                         "State resource mode attribute should "
                         "have been 'boot'")

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.validate_resource(test_resource, dirty=False)

    def test_expect_and_assert_case_run(self):
        """Test a TestCase that uses both expect and assert.

        * Defines the registered resource as required resource.
        * Runs the test under a test suite.
        * Validates that the test failed.
        * Validates the case's data object.
        * Validates the resource's state.
        """
        TempStoreFailureCase.resources = (request('test_resource',
                                               DemoResource,
                                               name=RESOURCE_NAME,
                                               dirty=False,),)

        case = self._run_case(TempStoreFailureCase)

        self.assertFalse(self.result.wasSuccessful(),
                         'Case succeeded when it should have failed')

        # === Validate case data object ===
        self.assertFalse(case.data.success,
                         'Case data result should have been False')

        self.assertEqual(case.data.exception_type, TestOutcome.FAILED,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.FAILED, case.data.exception_type))

        expected_traceback = "%s.*" % TempStoreFailureCase.FAILURE_MESSAGE
        match = re.search(expected_traceback, case.data.traceback,
                          flags=re.DOTALL)

        self.assertIsNotNone(match,
                     "Unexpected traceback, %r doesn't match the expression %r"
                     % (case.data.traceback, expected_traceback))

        test_resource = case.locked_resources[self.DEMO_RESOURCE_NAME]

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.validate_resource(test_resource, dirty=False)

    def test_stored_multiple_failures_case_run(self):
        """Test a TestCase that stores failures.

        * Defines the registered resource as required resource.
        * Runs the test under a test suite.
        * Validates that the test failed.
        * Validates the case's data object.
        * Validates the resource's state.
        """
        TempStoreMultipleFailuresCase.resources = (request('test_resource',
                                                        DemoResource,
                                                        name=RESOURCE_NAME,
                                                        dirty=False,),)

        case = self._run_case(TempStoreMultipleFailuresCase)

        self.assertFalse(self.result.wasSuccessful(),
                         'Case succeeded when it should have failed')

        # === Validate case data object ===
        self.assertFalse(case.data.success,
                         'Case data result should have been False')

        self.assertEqual(case.data.exception_type, TestOutcome.FAILED,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.FAILED, case.data.exception_type))

        expected_traceback = "%s.*%s.*%s.*" % (
                             TempStoreMultipleFailuresCase.FAILURE_MESSAGE1,
                             CaseData.TB_SEPARATOR,
                             TempStoreMultipleFailuresCase.FAILURE_MESSAGE2)

        match = re.search(expected_traceback, case.data.traceback,
                          flags=re.DOTALL)

        self.assertIsNotNone(match,
                     "Unexpected traceback, %r doesn't match the expression %r"
                     % (case.data.traceback, expected_traceback))

        test_resource = case.locked_resources[self.DEMO_RESOURCE_NAME]

        self.assertTrue(isinstance(test_resource, DemoResource),
                "State resource type should have been 'DemoResource'")

        self.assertEqual(test_resource.mode,
                         DemoResourceData.BOOT_MODE,
                         "State resource mode attribute should "
                         "have been 'boot'")

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.validate_resource(test_resource, dirty=False)

    def test_error_and_stored_failure_case_run(self):
        """Test a TestCase on that stores a failure and raises an exception.

        * Defines the registered resource as required resource.
        * Runs the test under a test suite.
        * Validates that the test fails.
        * Validates the case's data object.
        * Validates the resource's state.
        """
        TempStoreFailureErrorCase.resources = (request('test_resource',
                                                    DemoResource,
                                                    name=RESOURCE_NAME,
                                                    dirty=False,),)

        case = self._run_case(TempStoreFailureErrorCase)

        self.assertFalse(self.result.wasSuccessful(),
                         'Case succeeded when it should have failed')

        # === Validate case data object ===
        self.assertFalse(case.data.success,
                         'Case data result should have been False')

        self.assertEqual(case.data.exception_type, TestOutcome.ERROR,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.ERROR, case.data.exception_type))

        expected_traceback = "%s.*%s.*%s.*" % (
                                 TempStoreFailureErrorCase.FAILURE_MESSAGE,
                                 CaseData.TB_SEPARATOR,
                                 TempStoreFailureErrorCase.ERROR_MESSAGE)

        match = re.search(expected_traceback, case.data.traceback,
                          flags=re.DOTALL)

        self.assertIsNotNone(match,
                     "Unexpected traceback, %r doesn't match the expression %r"
                     % (case.data.traceback, expected_traceback))

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.validate_resource(test_resource, dirty=True)

    def test_errored_case_run(self):
        """Test a TestCase on run error.

        * Defines the registered resource as required resource.
        * Runs the test under a test suite.
        * Validates that the test fails.
        * Validates the case's data object.
        * Validates the resource's state.
        """
        TempErrorCase.resources = (request('test_resource',
                                        DemoResource,
                                        name=RESOURCE_NAME,
                                        dirty=False,),)

        case = self._run_case(TempErrorCase)

        self.assertFalse(self.result.wasSuccessful(),
                         'Case succeeded when it should have failed')

        # === Validate case data object ===
        self.assertFalse(case.data.success,
                         'Case data result should have been False')

        self.assertEqual(case.data.exception_type, TestOutcome.ERROR,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.ERROR, case.data.exception_type))

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.validate_resource(test_resource, dirty=True)

    def test_error_in_setup(self):
        """Test a TestCase on setup error.

        * Defines the registered resource as required resource.
        * Runs the test under a test suite.
        * Validates that the test fails.
        * Validates the case's data object.
        * Validates the resource's state.
        """
        TempErrorInSetupCase.resources = (request('test_resource',
                                               DemoResource,
                                               name=RESOURCE_NAME,
                                               dirty=False,),)

        case = self._run_case(TempErrorInSetupCase)

        self.assertFalse(self.result.wasSuccessful(),
                         'Case succeeded when it should have failed')

        # === Validate case data object ===
        self.assertFalse(case.data.success,
                         'Case data result should have been False')

        self.assertEqual(case.data.exception_type, TestOutcome.ERROR,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.ERROR, case.data.exception_type))

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.validate_resource(test_resource, dirty=True,
                               initialized=True, finalized=True)

    def test_error_in_resource_initialize_good_first(self):
        """Test a TestCase on resource initialization error on the second.

        * Defines the registered resources as required resource.
        * Runs the test under a test suite.
        * Validates that the test fails.
        * Validates the case's data object.
        * Validates the resources' state.
        """
        fail_resource_name = 'fail_initialize_resource'
        TempSuccessCase.resources = (request('ok_resource',
                                          DemoResource,
                                          name=RESOURCE_NAME,
                                          dirty=False,),
                                  request('fail_resource',
                                          DemoResource,
                                          name=fail_resource_name,
                                          dirty=False,))

        case = self._run_case(TempSuccessCase)

        self.assertFalse(self.result.wasSuccessful(),
                         'Case succeeded when it should have failed')

        # === Validate case data object ===
        self.assertFalse(case.data.success,
                         'Case data result should have been False')

        self.assertEqual(case.data.exception_type, TestOutcome.ERROR,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.ERROR, case.data.exception_type))

        ok_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)
        fail_resource = DemoResourceData.objects.get(name=fail_resource_name)

        self.validate_resource(ok_resource, dirty=True,
                               initialized=True, finalized=True)
        self.validate_resource(fail_resource, dirty=True,
                               initialized=False, finalized=True)

    def test_error_in_resource_initialize_bad_first(self):
        """Test a TestCase on resource initialization error on the first one.

        * Defines the registered resources as required resource.
        * Runs the test under a test suite.
        * Validates that the test fails.
        * Validates the case's data object.
        * Validates the resources' state.
        """
        fail_resource_name = 'fail_initialize_resource'
        TempSuccessCase.resources = (request('fail_resource',
                                          DemoResource,
                                          name=fail_resource_name,
                                          dirty=False,),
                                     request('ok_resource',
                                          DemoResource,
                                          name=RESOURCE_NAME,
                                          dirty=False,))

        case = self._run_case(TempSuccessCase)

        self.assertFalse(self.result.wasSuccessful(),
                         'Case succeeded when it should have failed')

        # === Validate case data object ===
        self.assertFalse(case.data.success,
                         'Case data result should have been False')

        self.assertEqual(case.data.exception_type, TestOutcome.ERROR,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.ERROR, case.data.exception_type))

        ok_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)
        fail_resource = DemoResourceData.objects.get(name=fail_resource_name)

        self.validate_resource(fail_resource, dirty=True,
                               initialized=False, finalized=True)
        self.validate_resource(ok_resource, dirty=False,
                               initialized=False, finalized=False)

    def test_error_in_resource_finalize(self):
        """Test a TestCase on resource finalization error.

        * Defines the registered resources as required resource.
        * Runs the test under a test suite.
        * Validates that the test fails.
        * Validates the case's data object.
        * Validates the resource's state.
        """
        fail_resource_name = 'fail_finalize_resource'
        TempSuccessCase.resources = (request('fail_resource',
                                          DemoResource,
                                          name=fail_resource_name,
                                          dirty=False,),
                                  request('ok_resource',
                                          DemoResource,
                                          name=RESOURCE_NAME,
                                          dirty=False,))

        case = self._run_case(TempSuccessCase)

        self.assertFalse(self.result.wasSuccessful(),
                         'Case succeeded when it should have failed')

        # === Validate case data object ===
        self.assertFalse(case.data.success,
                         'Case data result should have been False')

        self.assertEqual(case.data.exception_type, TestOutcome.ERROR,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.ERROR, case.data.exception_type))

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)
        fail_resource = DemoResourceData.objects.get(name=fail_resource_name)

        self.validate_resource(test_resource, dirty=False,
                               initialized=True, finalized=True)
        self.validate_resource(fail_resource, dirty=True,
                               initialized=True, finalized=False)

    def test_expected_failure_case_run(self):
        """Test a TestCase run on expected failure.

        * Defines the registered resource as required resource.
        * Runs the test under a test suite.
        * Validates that the test fails as expected.
        * Validates the case's data object.
        * Validates the resource's state.
        """
        TempExpectedFailureCase.resources = (request('test_resource',
                                                     DemoResource,
                                                     name=RESOURCE_NAME,
                                                     dirty=False,),)

        case = self._run_case(TempExpectedFailureCase)

        self.assertTrue(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        # === Validate case data object ===
        self.assertTrue(case.data.success,
                         'Case data result should have been True')

        self.assertEqual(case.data.exception_type,
                         TestOutcome.EXPECTED_FAILURE,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.EXPECTED_FAILURE,
                          case.data.exception_type))

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.validate_resource(test_resource, dirty=False)

    def test_unexpected_success_case_run(self):
        """Test a TestCase run on unexpected success.

        * Defines the registered resource as required resource.
        * Runs the test under a test suite.
        * Validates that the test succeeds.
        * Validates the case's data object.
        * Validates the resource's state.
        """
        TempUnexpectedSuccessCase.resources = (request('test_resource',
                                                       DemoResource,
                                                       name=RESOURCE_NAME,
                                                       dirty=False,),)

        case = self._run_case(TempUnexpectedSuccessCase)

        self.assertTrue(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        # === Validate case data object ===
        self.assertFalse(case.data.success,
                        'Case data result should have been True')

        self.assertEqual(case.data.exception_type,
                         TestOutcome.UNEXPECTED_SUCCESS,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.UNEXPECTED_SUCCESS,
                          case.data.exception_type))

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.validate_resource(test_resource, dirty=False)

    def test_missing_resource(self):
        """Test a TestCase with a missing required resource.

        * Defines a missing resource as required resource.
        * Runs the test under a test suite
        * Validates that the test failed.
        """
        TempSuccessCase.resources = (request('missing_resource',
                                             NonExistingResource,
                                             name='missing'),)

        case = self._run_case(TempSuccessCase)

        # === Validate case data object ===
        self.assertFalse(case.data.success)
        self.assertEqual(case.data.exception_type, TestOutcome.SKIPPED,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.SKIPPED, case.data.exception_type))

    def test_locked_resource(self):
        """Test a TestCase with a locked required resource.

        * Locks a resource using the resource manager.
        * Defines one available and one locked resource as required resources.
        * Runs the test under a test suite.
        * Validates the result is failure and the resources' state.
        """
        available_resource_name = 'available_resource2'
        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)
        test_resource.owner = self.FAKE_OWNER
        test_resource.save()

        TempSuccessCase.resources = (request('available_resource1',
                                          DemoResource,
                                          name=available_resource_name),
                                     request('locked_resource',
                                          DemoResource,
                                          name=RESOURCE_NAME))

        case = self._run_case(TempSuccessCase)

        # === Validate case data object ===
        self.assertFalse(case.data.success)
        self.assertEqual(case.data.exception_type, TestOutcome.SKIPPED,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.SKIPPED, case.data.exception_type))

        available_resource = DemoResourceData.objects.get(
                                                name=available_resource_name)
        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.validate_resource(test_resource, dirty=False,
                               initialized=False, finalized=False)

        self.validate_resource(available_resource, dirty=False,
                               initialized=False, finalized=False)

    def test_store_state(self):
        """Test the resource store sate method.

        * Define a resource as required resource.
        * Run the test under a test suite.
        * Validate store_state method was called (it writes a file).
        """
        resource_name = 'store_resource'
        TempSuccessCase.resources = (request(resource_name=resource_name,
                                             resource_class=DemoResource,
                                             name=RESOURCE_NAME),)

        case = self._run_case(TempSuccessCase)

        test_resource = case.locked_resources.values()[0]
        expected_state_path = os.path.join(test_resource.work_dir,
                                       ClientResourceManager.DEFAULT_STATE_DIR)

        self.assertTrue(os.path.exists(expected_state_path))

    def test_save_state(self):
        """Test the save_sate flag.

        * Defines a resource as required resource that not save state.
        * Runs the test under a test suite.
        * Validates store_state method wasn't called.
        """
        resource_name = 'save_state_resource'
        TempSuccessCase.resources = (request(resource_name=resource_name,
                                              resource_class=DemoResource,
                                              name=RESOURCE_NAME,
                                              save_state=False),)

        case = self._run_case(TempSuccessCase)
        expected_state_path = os.path.join(case.work_dir,
                                       ClientResourceManager.DEFAULT_STATE_DIR)

        self.assertFalse(os.path.exists(expected_state_path))

    def test_force_validate(self):
        """Tests the force_validate flag.

        Note:
            DemoResource fixture sets the 'validate_flag' as False.

        * Defines a resource as required resource & set force_validate.
        * Runs the test under a test suite.
        * Validates that 'validate' method was called.
        """
        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)
        self.assertIsNone(test_resource.validate_flag)

        TempSuccessCase.resources = (request(
                                          resource_name='validate_resource',
                                          resource_class=DemoResource,
                                          force_validate=True,
                                          name=RESOURCE_NAME),)

        self._run_case(TempSuccessCase)

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)
        self.assertTrue(test_resource.validate_flag, "Validation Failed.")

    def test_validate_after_test_error(self):
        """Tests error causes dirty flag and validation (in next test).

        Note:
            DemoResouce fixture sets the 'validate_flag' as None.

        * Defines a resource as required resource.
        * Runs an error test under a test suite.
        * Validates resource is dirty.
        * Defines a resource as required resource.
        * Runs a test under a test suite.
        * Validates that 'validate' method was called.
        """
        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.assertIsNone(test_resource.validate_flag)
        self.assertFalse(test_resource.dirty)

        TempErrorCase.resources = (request(resource_name='validate_resource',
                                        resource_class=DemoResource,
                                        force_validate=False,
                                        name=RESOURCE_NAME),)

        self._run_case(TempErrorCase)

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)
        self.assertTrue(test_resource.dirty)

        TempSuccessCase.resources = (request(
                                          resource_name='validate_resource',
                                          resource_class=DemoResource,
                                          force_validate=False,
                                          name=RESOURCE_NAME),)

        self._run_case(TempSuccessCase)

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.assertIsNotNone(test_resource.validate_flag,
                             "resource wasn't validated")
        self.assertTrue(test_resource.validate_flag, "Validation Failed.")

    def test_non_validate_after_test_failure(self):
        """Tests failure does not cause dirty flag or validation(in next test).

        Note:
            DemoResouce fixture sets the 'validate_flag' as None.

        * Define a resource as required resource.
        * Run a failure test under a test suite.
        * Validate resource is not dirty.
        * Define a resource as required resource.
        * Run a test under a test suite.
        * Validate that 'validate' method was not called.
        """
        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.assertIsNone(test_resource.validate_flag)

        TempFailureCase.resources = (request(
                                          resource_name='validate_resource',
                                          resource_class=DemoResource,
                                          force_validate=False,
                                          name=RESOURCE_NAME),)

        self._run_case(TempFailureCase)

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)
        self.assertFalse(test_resource.dirty)

        TempSuccessCase.resources = (request(
                                          resource_name='validate_resource',
                                          resource_class=DemoResource,
                                          force_validate=False,
                                          name=RESOURCE_NAME),)

        self._run_case(TempSuccessCase)

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)
        self.assertIsNone(test_resource.validate_flag)

    def test_non_validate_after_test_success(self):
        """Tests success does not cause dirty flag / validation (in next test).

        Note:
            DemoResouce fixture sets the 'validate_flag' as None.

        * Define a resource as required resource.
        * Run a test under a test suite.
        * Validate resource is not dirty.
        * Define a resource as required resource.
        * Run a test under a test suite.
        * Validate that 'validate' method was not called.
        """
        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)
        self.assertIsNone(test_resource.validate_flag)

        TempSuccessCase.resources = (request(
                                          resource_name='validate_resource',
                                          resource_class=DemoResource,
                                          force_validate=False,
                                          name=RESOURCE_NAME),)

        self._run_case(TempSuccessCase)

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)
        self.assertFalse(test_resource.dirty)

        TempSuccessCase.resources = (request(
                                          resource_name='validate_resource',
                                          resource_class=DemoResource,
                                          force_validate=False,
                                          name=RESOURCE_NAME),)

        self._run_case(TempSuccessCase)

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)
        self.assertIsNone(test_resource.validate_flag)

    def test_no_resource(self):
        """Test a TestCase with no required resource.

        * Defines no required resource.
        * Runs the test under a test suite.
        * Validates the result is success.
        """
        TempSuccessCase.resources = ()

        case = self._run_case(TempSuccessCase)

        # === Validate case data object ===
        self.assertTrue(case.data.success)
        self.assertEqual(case.data.exception_type, TestOutcome.SUCCESS,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.SUCCESS, case.data.exception_type))


if __name__ == '__main__':
    django.setup()
    colored_main(defaultTest='TestTestCase')
