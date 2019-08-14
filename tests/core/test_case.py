"""Test Rotest's TestCase class behavior."""
# pylint: disable=missing-docstring,unused-argument,protected-access
# pylint: disable=no-member,no-self-use,too-many-public-methods,invalid-name
# pylint: disable=too-many-lines
from __future__ import absolute_import

import os
import re
import six

from future.builtins import next
from future.utils import iteritems

from rotest.core.case import request
from rotest.core.models.case_data import TestOutcome, CaseData
from rotest.management.models.ut_models import DemoResourceData
from rotest.management.models.ut_resources import (DemoResource,
                                                   DemoResource2,
                                                   ResourceAdapter,
                                                   NonExistingResource,
                                                   DemoComplexResource,
                                                   DemoAdaptiveComplexResource)

from tests.core.utils import (ErrorInSetupCase, SuccessCase, FailureCase,
                              ErrorCase, StoreMultipleFailuresCase,
                              UnexpectedSuccessCase, BasicRotestUnitTest,
                              DynamicResourceLockingCase, ExpectRaisesCase,
                              StoreFailureErrorCase, ExpectedFailureCase,
                              StoreFailureCase, MockTestSuite, SkipCase)


RESOURCE_NAME = 'available_resource1'


class TempSuccessCase(SuccessCase):
    """Inherit class and override resources requests."""
    __test__ = False

    resources = (request('test_resource', DemoResource, name=RESOURCE_NAME),)


class TempSkipCase(SkipCase):
    """Inherit class and override resources requests."""
    __test__ = False

    resources = (request('test_resource', DemoResource, name=RESOURCE_NAME),)


class TempComplexRequestCase(SuccessCase):
    """Inherit class and override resources requests."""
    __test__ = False

    resources = (request('res1', DemoResource, name='available_resource1'),)
    res2 = DemoResource.request(name='available_resource2')


class TempComplexAdaptiveResourceCase(SuccessCase):
    """Inherit class and override resources requests."""
    __test__ = False

    resources = (request('res1', DemoAdaptiveComplexResource),)


class TempAdaptiveRequestPositiveCase(SuccessCase):
    """Inherit class and override resources requests."""
    __test__ = False

    resources = ()
    res = ResourceAdapter(config_key='field1',
                          resource_classes={False: DemoResource,
                                            True: DemoComplexResource},
                          name='available_resource1')


class TempAdaptiveRequestNegativeCase(SuccessCase):
    """Inherit class and override resources requests."""
    __test__ = False

    resources = ()
    res = ResourceAdapter(config_key='field1',
                          resource_classes={True: DemoResource,
                                            False: DemoComplexResource},
                          name='available_resource1')


class TempInheritRequestCase(TempComplexRequestCase):
    """Inherit one resource requests from the parent class."""
    __test__ = False

    resources = ()


class TempDynamicResourceLockingCase(DynamicResourceLockingCase):
    """Inherit class and override resources requests."""
    __test__ = False

    resources = (request('test_resource', DemoResource, name=RESOURCE_NAME),)


class TempFailureCase(FailureCase):
    """Inherit class and override resources requests."""
    __test__ = False

    resources = (request('test_resource', DemoResource, name=RESOURCE_NAME),)


class TempStoreFailureCase(StoreFailureCase):
    """Inherit class and override resources requests."""
    __test__ = False

    resources = (request('test_resource', DemoResource, name=RESOURCE_NAME),)


class TempExpectRaisesCase(ExpectRaisesCase):
    """Inherit class and override resources requests."""
    __test__ = False

    resources = (request('test_resource', DemoResource, name=RESOURCE_NAME),)


class TempErrorCase(ErrorCase):
    """Inherit class and override resources requests."""
    __test__ = False

    resources = (request('test_resource', DemoResource, name=RESOURCE_NAME),)


class TempStoreFailureErrorCase(StoreFailureErrorCase):
    """Inherit class and override resources requests."""
    __test__ = False

    resources = (request('test_resource', DemoResource, name=RESOURCE_NAME),)


class TempErrorInSetupCase(ErrorInSetupCase):
    """Inherit class and override resources requests."""
    __test__ = False

    resources = (request('test_resource', DemoResource, name=RESOURCE_NAME),)


class TempExpectedFailureCase(ExpectedFailureCase):
    """Inherit class and override resources requests."""
    __test__ = False

    resources = (request('test_resource', DemoResource, name=RESOURCE_NAME),)


class TempUnexpectedSuccessCase(UnexpectedSuccessCase):
    """Inherit class and override resources requests."""
    __test__ = False

    resources = (request('test_resource', DemoResource, name=RESOURCE_NAME),)


class TempStoreMultipleFailuresCase(StoreMultipleFailuresCase):
    """Inherit class and override resources requests."""
    __test__ = False

    resources = (request('test_resource', DemoResource, name=RESOURCE_NAME),)


class ForceReleaseCase(SuccessCase):
    """Inherit class and override force initialize flag."""
    __test__ = False

    resources = (request('test_resource', DemoResource, name=RESOURCE_NAME),)

    def request_resources(self, resources_to_request, use_previous=False,
                          force_initialize=False):
        return super(ForceReleaseCase, self).request_resources(
            resources_to_request, use_previous, True)


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

    def _run_case(self, test_case, **kwargs):
        """Run given case and return it.

        Args:
            test_case (rotest.core.case.TestCase): case to run.

        Returns:
            rotest.core.case.TestCase. the case.
        """
        class InternalSuite(MockTestSuite):
            components = (test_case,)

        test_suite = InternalSuite()
        case = test_suite._tests[0]
        for name, value in iteritems(kwargs):
            setattr(case, name, value)

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
                                             name=RESOURCE_NAME),)

        case = self._run_case(TempSuccessCase)

        self.assertTrue(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        # === Validate case data object ===
        self.assertTrue(case.data.success)

        self.assertEqual(case.data.exception_type, TestOutcome.SUCCESS,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.SUCCESS, case.data.exception_type))

        test_resource = case.all_resources[self.DEMO_RESOURCE_NAME]
        self.assertTrue(isinstance(test_resource, DemoResource),
                "State resource data type should have been 'DemoResourceData'")

        self.assertEqual(test_resource.mode,
                         DemoResourceData.BOOT_MODE,
                         "State resource mode attribute should "
                         "have been 'boot'")

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.validate_resource(test_resource)

    def test_complex_resource_request(self):
        """Test a TestCase with all the ways to request resources.

        * Way 1 - overriding 'resources'.
        * Way 2 - declaring fields with BaseResource instance.
        """
        case = self._run_case(TempComplexRequestCase)

        self.assertTrue(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        # === Validate case data object ===
        self.assertTrue(case.data.success)

        test_resources = case.all_resources
        locked_names = []
        for resource in six.itervalues(test_resources):
            self.assertTrue(isinstance(resource, DemoResource),
                            "Got wrong resource %r for the request" % resource)

            test_resource = DemoResourceData.objects.get(name=resource.name)
            self.validate_resource(test_resource)
            locked_names.append(resource.name)

        self.assertEqual(len(test_resources), 2,
                         "Unexpected number of resources, expected %r got %r" %
                         (2, len(test_resources)))

        for request_name in ['res1', 'res2']:
            self.assertTrue(request_name in test_resources,
                            "Test didn't request a resource for %s" %
                            request_name)

            self.assertTrue(request_name in case.__dict__,
                            "Test doesn't contain field named %s" %
                            request_name)

        self.assertIn('available_resource1', locked_names,
                      "Resource request using 'resources' ignored kwargs")

        self.assertIn('available_resource2', locked_names,
                      "Resource request using class field ignored kwargs")

    def test_complex_adaptive_resource_request(self):
        """Test a TestCase that requests a complex adaptive resources."""
        case = self._run_case(TempComplexAdaptiveResourceCase,
                              config={'field1': False})

        self.assertTrue(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        # === Validate case data object ===
        self.assertTrue(case.data.success)

        test_resources = case.all_resources

        self.assertEqual(len(test_resources), 1,
                         "Unexpected number of resources, expected %r got %r" %
                         (1, len(test_resources)))

        resource, = list(test_resources.values())
        self.assertTrue(isinstance(resource.sub_res1, DemoResource2),
                        "Got wrong resource %r for sub_res1" % resource)
        self.assertTrue(isinstance(resource.sub_res2, DemoResource2),
                        "Got wrong resource %r for sub_res2" % resource)

    def test_inherit_resource_request(self):
        """Test a TestCase that inherits its resource request."""
        case = self._run_case(TempInheritRequestCase)

        self.assertTrue(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        # === Validate case data object ===
        self.assertTrue(case.data.success)

        test_resources = case.all_resources
        self.assertEqual(len(test_resources), 1,
                         "Unexpected number of resources, expected %r got %r" %
                         (1, len(test_resources)))

        request_name = 'res2'
        self.assertTrue(request_name in test_resources,
                        "Test didn't request a resource for %s" % request_name)

        self.assertTrue(request_name in case.__dict__,
                        "Test doesn't contain field named %s" %
                        request_name)

    def test_adaptive_request_positive(self):
        """Test a positive TestCase with a resource adapter.

        * Using the kwargs, ask for an existing resource.
        """
        case = self._run_case(TempAdaptiveRequestPositiveCase,
                              config={'field1': False})

        self.assertTrue(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        # === Validate case data object ===
        self.assertTrue(case.data.success)

        test_resources = case.all_resources
        locked_names = []
        for resource in six.itervalues(test_resources):
            self.assertTrue(isinstance(resource, DemoResource),
                            "Got wrong resource %r for the request" % resource)

            test_resource = DemoResourceData.objects.get(name=resource.name)
            self.validate_resource(test_resource)
            locked_names.append(resource.name)

        self.assertEqual(len(test_resources), 1,
                         "Unexpected number of resources, expected %r got %r" %
                         (1, len(test_resources)))

        request_name = 'res'
        self.assertTrue(request_name in test_resources,
                        "Test didn't request a resource for %s" %
                        request_name)

        self.assertTrue(request_name in case.__dict__,
                        "Test doesn't contain field named %s" %
                        request_name)

        self.assertIn('available_resource1', locked_names,
                      "Resource request using 'resources' ignored kwargs")

    def test_adaptive_request_negative(self):
        """Test a negative TestCase with a resource adapter.

        * Using the kwargs, ask for a non existing resource.
        """
        case = self._run_case(TempAdaptiveRequestNegativeCase,
                              config={'field1': False})

        self.assertFalse(self.result.wasSuccessful(),
                         'Case failed when it should have succeeded')

        # === Validate case data object ===
        self.assertFalse(case.data.success)

        test_resources = case.all_resources
        self.assertEqual(len(test_resources), 0,
                         "Unexpected number of resources, expected %r got %r" %
                         (0, len(test_resources)))

    def test_dynamic_resources_locking(self):
        """Test that cases can dynamically lock resources.

        * Run a test that dynamically requests resources.
        * Validate that the resources were initialized and finalized.
        """
        TempDynamicResourceLockingCase.resources = (request('test_resource',
                                                         DemoResource,
                                                         name=RESOURCE_NAME),)
        dynamic_resource_name = 'available_resource2'
        TempDynamicResourceLockingCase.dynamic_resources = (
                                                 request('dynamic_resource',
                                                 DemoResource,
                                                 name=dynamic_resource_name),)

        case = self._run_case(TempDynamicResourceLockingCase)

        self.assertTrue(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        # === Validate case data object ===
        self.assertTrue(case.data.success)

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)
        self.validate_resource(test_resource)
        test_resource = DemoResourceData.objects.get(
                                                 name=dynamic_resource_name)
        self.validate_resource(test_resource)

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
                                             name=RESOURCE_NAME),)

        case = self._run_case(TempFailureCase)

        self.assertFalse(self.result.wasSuccessful(),
                         'Case succeeded when it should have failed')

        # === Validate case data object ===
        self.assertFalse(case.data.success,
                         'Case data result should have been False')

        self.assertEqual(case.data.exception_type, TestOutcome.FAILED,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.FAILED, case.data.exception_type))

        test_resource = case.all_resources[self.DEMO_RESOURCE_NAME]

        self.assertTrue(isinstance(test_resource, DemoResource),
                "State resource type should have been 'DemoResource'")

        self.assertEqual(test_resource.mode,
                         DemoResourceData.BOOT_MODE,
                         "State resource mode attribute should "
                         "have been 'boot'")

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.validate_resource(test_resource)

    def test_expect_and_assert_case_run(self):
        """Test a TestCase that uses both expect and assert.

        * Defines the registered resource as required resource.
        * Runs the test under a test suite.
        * Validates that the test failed with both tracebacks.
        * Validates the case's data object.
        * Validates the resource's state.
        """
        TempStoreFailureCase.resources = (request('test_resource',
                                                  DemoResource,
                                                  name=RESOURCE_NAME),)

        case = self._run_case(TempStoreFailureCase)

        self.assertFalse(self.result.wasSuccessful(),
                         'Case succeeded when it should have failed')

        # === Validate case data object ===
        self.assertFalse(case.data.success,
                         'Case data result should have been False')

        self.assertEqual(case.data.exception_type, TestOutcome.FAILED,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.FAILED, case.data.exception_type))

        expected_traceback = "%s.*%s.*" % (StoreFailureCase.FAILURE_MESSAGE,
                                           StoreFailureCase.ASSERTION_MESSAGE)

        match = re.search(expected_traceback, case.data.traceback,
                          flags=re.DOTALL)

        self.assertIsNotNone(match,
                     "Unexpected traceback, %r doesn't match the expression %r"
                     % (case.data.traceback, expected_traceback))

        test_resource = case.all_resources[self.DEMO_RESOURCE_NAME]

        self.assertTrue(isinstance(test_resource, DemoResource),
                "State resource type should have been 'DemoResource'")

        self.assertEqual(test_resource.mode,
                         DemoResourceData.BOOT_MODE,
                         "State resource mode attribute should "
                         "have been 'boot'")

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.validate_resource(test_resource)

    def test_expect_raises_and_assert_case_run(self):
        """Test a TestCase that uses both expect raises and assert.

        * Defines the registered resource as required resource.
        * Runs the test under a test suite.
        * Validates that the test failed with three tracebacks.
        * Validates the case's data object.
        * Validates the resource's state.
        """
        TempExpectRaisesCase.resources = (request('test_resource',
                                                   DemoResource,
                                                   name=RESOURCE_NAME),)

        case = self._run_case(TempExpectRaisesCase)

        self.assertFalse(self.result.wasSuccessful(),
                         'Case succeeded when it should have failed')

        # === Validate case data object ===
        self.assertFalse(case.data.success,
                         'Case data result should have been False')

        self.assertEqual(case.data.exception_type, TestOutcome.FAILED,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.FAILED, case.data.exception_type))

        expected_traceback = "%s.*%s.*%s.*" %\
                             (TempExpectRaisesCase.FAILURE_MESSAGE,
                              TempExpectRaisesCase.FAILURE_MESSAGE,
                              TempExpectRaisesCase.ASSERTION_MESSAGE)

        match = re.search(expected_traceback, case.data.traceback,
                          flags=re.DOTALL)

        self.assertIsNotNone(match, "Unexpected traceback, "
                             "%r doesn't match the expression %r"
                             % (case.data.traceback, expected_traceback))

        test_resource = case.all_resources[self.DEMO_RESOURCE_NAME]

        self.assertTrue(isinstance(test_resource, DemoResource),
                        "State resource type should have been 'DemoResource'")

        self.assertEqual(test_resource.mode,
                         DemoResourceData.BOOT_MODE,
                         "State resource mode attribute should "
                         "have been 'boot'")

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.validate_resource(test_resource)

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
                                                        name=RESOURCE_NAME),)

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

        test_resource = case.all_resources[self.DEMO_RESOURCE_NAME]

        self.assertTrue(isinstance(test_resource, DemoResource),
                "State resource type should have been 'DemoResource'")

        self.assertEqual(test_resource.mode,
                         DemoResourceData.BOOT_MODE,
                         "State resource mode attribute should "
                         "have been 'boot'")

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.validate_resource(test_resource)

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
                                                       name=RESOURCE_NAME),)

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

        self.validate_resource(test_resource)

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
                                           name=RESOURCE_NAME),)

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

        self.validate_resource(test_resource)

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
                                                  name=RESOURCE_NAME),)

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

        self.validate_resource(test_resource,
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
                                             name=RESOURCE_NAME),
                                     request('fail_resource',
                                             DemoResource,
                                             name=fail_resource_name))

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

        self.validate_resource(ok_resource,
                               initialized=True, finalized=True)
        self.validate_resource(fail_resource,
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
                                             name=fail_resource_name),
                                     request('ok_resource',
                                             DemoResource,
                                             name=RESOURCE_NAME))

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

        self.validate_resource(fail_resource,
                               initialized=False, finalized=True)
        self.validate_resource(ok_resource, validated=False,
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
                                             name=fail_resource_name),
                                     request('ok_resource',
                                             DemoResource,
                                             name=RESOURCE_NAME))

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

        self.validate_resource(test_resource,
                               initialized=True, finalized=True)
        self.validate_resource(fail_resource,
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
                                                     name=RESOURCE_NAME),)

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

        self.validate_resource(test_resource)

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
                                                       name=RESOURCE_NAME),)

        case = self._run_case(TempUnexpectedSuccessCase)
        self.assertFalse(self.result.wasSuccessful(),
                        'Case succeeded when it should have failed')

        # === Validate case data object ===
        self.assertFalse(case.data.success,
                        'Case data result should have been True')

        self.assertEqual(case.data.exception_type,
                         TestOutcome.UNEXPECTED_SUCCESS,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.UNEXPECTED_SUCCESS,
                          case.data.exception_type))

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.validate_resource(test_resource)

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
        self.assertEqual(case.data.exception_type, TestOutcome.ERROR,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.ERROR, case.data.exception_type))

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
        self.assertEqual(case.data.exception_type, TestOutcome.ERROR,
                         "Unexpected test outcome, expected %r got %r" %
                         (TestOutcome.ERROR, case.data.exception_type))

        available_resource = DemoResourceData.objects.get(
                                                name=available_resource_name)
        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)

        self.validate_resource(test_resource, validated=False,
                               initialized=False, finalized=False)

        self.validate_resource(available_resource, validated=False,
                               initialized=False, finalized=False)

    def test_save_state_on_failed_test(self):
        """Test the usage of the save_state flag when a test has failed.

        When a test has failed it is expected that it WILL save the state.
        """
        resource_name = 'store_resource'
        TempErrorCase.resources = (request(resource_name=resource_name,
                                           resource_class=DemoResource,
                                           name=RESOURCE_NAME),)

        case = self._run_case(TempErrorCase, save_state=True)

        expected_state_path = os.path.join(case.work_dir,
                                           TempErrorCase.STATE_DIR_NAME)

        self.assertTrue(os.path.exists(expected_state_path))

    def test_save_state_on_passed_test(self):
        """Test the usage of the save_state flag when a test has passed.

        When a test has passed it is expected that it WILL NOT save the state.
        """
        resource_name = 'save_state_resource'
        TempSuccessCase.resources = (request(resource_name=resource_name,
                                             resource_class=DemoResource,
                                             name=RESOURCE_NAME),)

        case = self._run_case(TempSuccessCase, save_state=True)
        expected_state_path = os.path.join(case.work_dir,
                                           TempSuccessCase.STATE_DIR_NAME)

        self.assertFalse(os.path.exists(expected_state_path))

    def test_save_state_on_expected_failure_test(self):
        """Test the usage of the save_state flag when a test has
            passed with an expected failure.

        When a test has passed it is expected that it WILL NOT save the state.
        """
        resource_name = 'save_state_resource'
        TempExpectedFailureCase.resources = (
            request(resource_name=resource_name,
                    resource_class=DemoResource,
                    name=RESOURCE_NAME),)

        case = self._run_case(TempExpectedFailureCase, save_state=True)
        expected_state_path = os.path.join(
            case.work_dir, TempExpectedFailureCase.STATE_DIR_NAME)

        self.assertFalse(os.path.exists(expected_state_path))

    def test_save_state_on_skipped_test(self):
        """Test the usage of the save_state flag when a test was skipped.

        When a test has been skipped it is expected that it WILL NOT
            save the state.
        """
        resource_name = 'save_state_resource'
        TempSkipCase.resources = (request(resource_name=resource_name,
                                          resource_class=DemoResource,
                                          name=RESOURCE_NAME),)

        case = self._run_case(TempSkipCase, save_state=True)
        expected_state_path = os.path.join(case.work_dir,
                                           TempSkipCase.STATE_DIR_NAME)

        self.assertFalse(os.path.exists(expected_state_path))

    def test_force_initialize(self):
        """Tests the force_initialize flag when True.

        Note:
            DemoResource fixture sets the 'validate_flag' as False.

        * Defines a resource as required resource & set force_initialize.
        * Runs the test under a test suite.
        * Validates that 'validate' method was not called.
        * Validates that 'initialize' method was called.
        """
        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)
        self.assertFalse(test_resource.validate_flag)

        test_resource.validation_result = True
        test_resource.save()
        TempSuccessCase.resources = (request(
                                          resource_name='validate_resource',
                                          resource_class=DemoResource,
                                          name=RESOURCE_NAME),)

        self._run_case(ForceReleaseCase)

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)
        test_resource.validation_result = False
        test_resource.save()
        self.assertFalse(test_resource.validate_flag,
                         "Resource was unexpectedly validated")
        self.assertTrue(test_resource.initialization_flag,
                        "Resource wasn't initialized as expected")

    def test_skip_initialize(self):
        """Tests the force_initialize flag when False.

        Note:
            DemoResource fixture sets the 'validate_flag' as False.

        * Defines a resource as required resource & set force_initialize.
        * Runs the test under a test suite.
        * Validates that 'validate' method was called.
        * Validates that 'initialize' method was not called.
        """
        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)
        self.assertFalse(test_resource.validate_flag)

        test_resource.validation_result = True
        test_resource.save()
        TempSuccessCase.resources = (request(
                                          resource_name='validate_resource',
                                          resource_class=DemoResource,
                                          name=RESOURCE_NAME),)

        self._run_case(TempSuccessCase)

        test_resource = DemoResourceData.objects.get(name=RESOURCE_NAME)
        test_resource.validation_result = False
        test_resource.save()
        self.assertTrue(test_resource.validate_flag,
                        "Resource wasn't validated as expected")
        self.assertFalse(test_resource.initialization_flag,
                         "Resource was unexpectedly initialized")

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
