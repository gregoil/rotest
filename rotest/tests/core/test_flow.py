"""Test TestSuite behavior and common variables."""
import django

from rotest.core.case import request
from rotest.core.flow_component import PipeTo
from rotest.core.models.case_data import TestOutcome
from rotest.common.colored_test_runner import colored_main
from rotest.core.block import MODE_CRITICAL, MODE_FINALLY, MODE_OPTIONAL
from rotest.management.models.ut_models import (DemoResource,
                                                DemoResourceData,
                                                InitializeErrorResource)
from rotest.tests.core.utils import (FailureBlock, ErrorBlock, SuccessBlock,
                                     MockFlow, SkipBlock, ExpectedFailureBlock,
                                     UnexpectedSuccessBlock, NoMethodsBlock,
                                     InputsValidationBlock, WriteToCommonBlock,
                                     MultipleMethodsBlock, ReadFromCommonBlock,
                                     BasicRotestUnitTest, MockSubFlow,
                                     AttributeCheckingBlock, MockBlock,
                                     DynamicResourceLockingBlock,
                                     PretendToShareDataBlock)


class TestTestFlow(BasicRotestUnitTest):
    """Test TestFlow behavior on successful & failed components."""

    fixtures = ['case_ut.json']

    def validate_blocks(self, test_flow, successes=0, failures=0, errors=0,
                        skips=0, expected_failures=0, unexpected_successes=0):
        """Validate the result of the blocks under a flow."""
        blocks = list(test_flow)

        actual_successes = len([block for block in blocks if
                          block.data.exception_type == TestOutcome.SUCCESS])
        self.assertEqual(actual_successes, successes,
                         "Wrong number of successes (got %d, expected %d)" %
                         (actual_successes, successes))

        actual_failures = len([block for block in blocks if
                          block.data.exception_type == TestOutcome.FAILED])
        self.assertEqual(actual_failures, failures,
                         "Wrong number of failures (got %d, expected %d)" %
                         (actual_failures, failures))

        actual_errors = len([block for block in blocks if
                          block.data.exception_type == TestOutcome.ERROR])
        self.assertEqual(actual_errors, errors,
                         "Wrong number of errors (got %d, expected %d)" %
                         (actual_errors, errors))

        actual_skips = len([block for block in blocks if
                          block.data.exception_type == TestOutcome.SKIPPED])
        self.assertEqual(actual_skips, skips,
                         "Wrong number of skips (got %d, expected %d)" %
                         (actual_skips, skips))

        actual_expected_failures = len([block for block in blocks if
                  block.data.exception_type == TestOutcome.EXPECTED_FAILURE])
        self.assertEqual(actual_expected_failures, expected_failures,
                         "Wrong number of skips (got %d, expected %d)" %
                         (actual_expected_failures, expected_failures))

        actual_unexpected_successes = len([block for block in blocks if
              block.data.exception_type == TestOutcome.UNEXPECTED_SUCCESS])
        self.assertEqual(actual_unexpected_successes, unexpected_successes,
                         "Wrong number of skips (got %d, expected %d)" %
                         (actual_unexpected_successes, unexpected_successes))

    def test_empty_flow(self):
        """Test empty 'blocks' tuple raises AttributeError."""
        MockFlow.blocks = ()
        self.assertRaises(AttributeError, MockFlow)

    def test_too_many_test_methods_block(self):
        """Test blocks with more than one test method raises AttributeError."""
        MockFlow.blocks = (MultipleMethodsBlock,)
        self.assertRaises(AttributeError, MockFlow)

    def test_no_test_methods_block(self):
        """Test blocks with no test methods raises AttributeError."""
        MockFlow.blocks = (NoMethodsBlock,)
        self.assertRaises(AttributeError, MockFlow)

    def test_invalid_type(self):
        """Test invalid block type raises TypeError."""
        class BadTestType():
            pass

        MockFlow.blocks = (SuccessBlock, BadTestType, SuccessBlock)

        self.assertRaises(TypeError, MockFlow)

    def test_happy_flow(self):
        """Create test flow with success components & validate run success.

        We test the flow result was success and that all the components run.
        """
        MockFlow.blocks = (SuccessBlock, SuccessBlock)

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.assertEqual(self.result.testsRun, 1,
                         "Flow didn't run the correct number of blocks")

        self.validate_blocks(test_flow, successes=2)

        # === Validate data object ===
        self.assertTrue(test_flow.data.success,
                        'Flow data result should have been True')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.SUCCESS,
                        'Flow data status should have been success')

    def test_skip_alone(self):
        """Create test flow with only skipped blocks and test its behavior."""
        MockFlow.blocks = (SkipBlock, SkipBlock)

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.assertEqual(self.result.testsRun, 1,
                         "Flow didn't run the correct number of blocks")

        self.validate_blocks(test_flow, skips=2)

        # === Validate data object ===
        self.assertEqual(test_flow.data.success, True,
                        'Flow data result should have been None')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.SUCCESS,
                        'Flow data status should have been success')

    def test_skip_and_success(self):
        """Validate test flow with success and skipped blocks."""
        MockFlow.blocks = (SkipBlock, SuccessBlock)

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.assertEqual(self.result.testsRun, 1,
                         "Flow didn't run the correct number of blocks")

        self.validate_blocks(test_flow, successes=1, skips=1)

        # === Validate data object ===
        self.assertTrue(test_flow.data.success,
                        'Flow data result should have been True')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.SUCCESS,
                        'Flow data status should have been success')

    def test_flow_failure(self):
        """Create test flow with failed component & validate its behavior.

        We test the flow result was failure and all the component run.
        """
        MockFlow.blocks = (SuccessBlock, FailureBlock)

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertFalse(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 1,
                         "Result didn't run the correct number of tests")

        self.assertEqual(len(self.result.failures), 1,
                         "Result didn't fail the correct number of tests")

        self.validate_blocks(test_flow, successes=1, failures=1)

        # === Validate data object ===
        self.assertFalse(test_flow.data.success,
                         'Flow data result should have been False')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.FAILED,
                        'Flow data status should have been failure')

    def test_flow_error(self):
        """Create test flow with error component & validate its behavior.

        We test the flow result was error and all the component run.
        """
        MockFlow.blocks = (SuccessBlock, ErrorBlock)

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertFalse(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 1,
                         "Result didn't run the correct number of tests")

        self.assertEqual(len(self.result.errors), 1,
                         "Result didn't had the correct number of errors")

        self.validate_blocks(test_flow, successes=1, errors=1)

        # === Validate data object ===
        self.assertFalse(test_flow.data.success,
                         'Flow data result should have been False')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.ERROR,
                        'Flow data status should have been error')

    def test_expected_failure(self):
        """Create test flow with expected failure block and validate behavior.

        We test the flow result was success and that all the components run.
        """
        MockFlow.blocks = (SuccessBlock, ExpectedFailureBlock)

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.assertEqual(self.result.testsRun, 1,
                         "Flow didn't run the correct number of blocks")

        self.validate_blocks(test_flow, successes=1, expected_failures=1)

        # === Validate data object ===
        self.assertTrue(test_flow.data.success,
                        'Flow data result should have been True')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.SUCCESS,
                        'Flow data status should have been success')

    def test_unexpected_success(self):
        """Create test flow with unexpected success block and check behavior.

        We test the flow result was failure and all the component run.
        """
        MockFlow.blocks = (SuccessBlock, UnexpectedSuccessBlock)

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertFalse(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 1,
                         "Result didn't run the correct number of tests")

        self.assertEqual(len(self.result.failures), 1,
                         "Result didn't fail the correct number of tests")

        self.validate_blocks(test_flow, successes=1, unexpected_successes=1)

        # === Validate data object ===
        self.assertFalse(test_flow.data.success,
                         'Flow data result should have been False')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.FAILED,
                        'Flow data status should have been failure')

    def test_inputs_happy_flow(self):
        """Test behavior of inputs validation of blocks in positive case.

        * The flow locks a resource.
        * It's first block shares a value.
        * The second block validates it has both the result and the shared
            value using the 'inputs' field.
        """
        InputsValidationBlock.inputs = ('res1', WriteToCommonBlock.INJECT_NAME)
        MockFlow.blocks = (WriteToCommonBlock,
                           InputsValidationBlock)

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.validate_blocks(test_flow, successes=2)

    def test_shared_data_priority(self):
        """Test that shared data has higher priority than class fields."""
        class BlockWithOptionalField(ReadFromCommonBlock):
            pass

        # Set class field
        STATIC_VALUE = 'static_value'
        setattr(BlockWithOptionalField,
                WriteToCommonBlock.INJECT_NAME, STATIC_VALUE)

        # Block to check that the correct value is injected into the block
        BlockWithOptionalField.READ_NAME = WriteToCommonBlock.INJECT_NAME
        BlockWithOptionalField.READ_VALUE = WriteToCommonBlock.INJECT_VALUE

        MockFlow.blocks = (WriteToCommonBlock,
                           BlockWithOptionalField)

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.validate_blocks(test_flow, successes=2)

    def test_inputs_initial_data(self):
        """Check that test-flows' initial common data is injected at start."""
        PARAMETER_VALUE = 'some_value2'
        PARAMETER_NAME = 'some_parameter2'

        class FlowWithCommon(MockFlow):
            common = {PARAMETER_NAME: PARAMETER_VALUE}

        # Block to check that input validates the parameter
        InputsValidationBlock.inputs = ('res1', PARAMETER_NAME)

        # Block to check that the correct value is injected into the block
        ReadFromCommonBlock.READ_NAME = PARAMETER_NAME
        ReadFromCommonBlock.READ_VALUE = PARAMETER_VALUE

        FlowWithCommon.blocks = (InputsValidationBlock,
                                 ReadFromCommonBlock)

        test_flow = FlowWithCommon()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.validate_blocks(test_flow, successes=2)

    def test_inputs_static_check(self):
        """Test static check of inputs validation of blocks.

        Run a flow with a block that expects an input it doesn't get,
        then expect it to have an error.
        """
        missing_input_name = 'noinput'
        InputsValidationBlock.inputs = (missing_input_name,)

        MockFlow.blocks = (InputsValidationBlock,)

        with self.assertRaises(AttributeError):
            MockFlow()

    def test_inputs_dynamic_check(self):
        """Test runtime validation of inputs of blocks.

        Run a flow with a block that pretends to share data and a block that
        needs this data as an input.
        """
        pass_value = 'not_exist_value'
        PretendToShareDataBlock.outputs = (pass_value,)
        InputsValidationBlock.inputs = (pass_value, )

        MockFlow.blocks = (PretendToShareDataBlock, InputsValidationBlock)
        test_flow = MockFlow()

        self.run_test(test_flow)
        self.assertEqual(len(self.result.errors), 1,
                         "Result didn't had the correct number of errors")

    def test_inputs_static_check_with_pipe(self):
        """Test static check of inputs validation of blocks when using pipes.

        Run a flow with a block that expects an piped input it doesn't get,
        then expect it to have an error.
        """
        missing_input_name = 'noinput'
        InputsValidationBlock.inputs = (missing_input_name,)

        MockFlow.blocks = (InputsValidationBlock.params(
                            noinput=PipeTo(WriteToCommonBlock.INJECT_NAME)),)

        with self.assertRaises(AttributeError):
            MockFlow()

    def test_parametrize(self):
        """Validate parametrize behavior.

        * Checks that passing values via parametrize passes the 'inputs' check.
        * Checks that the values set via parametrize are correct.
        * Checks that passing values via parametrize is local to the block.
        """
        PARAMETER_VALUE = 'some_value'
        PARAMETER_NAME = 'some_parameter'
        parameters = {PARAMETER_NAME: PARAMETER_VALUE}

        # Block to check that input validates the parameter
        InputsValidationBlock.inputs = ('res1', PARAMETER_NAME)

        # Block to check that the correct value is injected into the block
        ReadFromCommonBlock.READ_NAME = PARAMETER_NAME
        ReadFromCommonBlock.READ_VALUE = PARAMETER_VALUE

        MockFlow.blocks = (InputsValidationBlock.params(**parameters),
                           ReadFromCommonBlock.params(**parameters),
                           ReadFromCommonBlock)

        test_flow = MockFlow()
        self.run_test(test_flow)

        # The third block should get an error since it wasn't injected with
        # the parameters and it tries to read them.
        self.assertFalse(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.validate_blocks(test_flow, successes=2, errors=1)

    def test_pipes_happy_flow(self):
        """Validate parametrize behavior when using pipes."""
        # Block to check that the correct value is wrote through the pipe
        ReadFromCommonBlock.READ_NAME = 'pipe_parameter'
        ReadFromCommonBlock.READ_VALUE = WriteToCommonBlock.INJECT_VALUE

        MockFlow.blocks = (WriteToCommonBlock,
                           ReadFromCommonBlock.params(pipe_parameter=
                               PipeTo(WriteToCommonBlock.INJECT_NAME)))

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.validate_blocks(test_flow, successes=2)

    def test_setup_flow(self):
        """Check that test-flows' setUp method is called before the blocks."""
        PARAMETER_VALUE = 'some_value2'
        PARAMETER_NAME = 'some_parameter2'

        class FlowWithSetup(MockFlow):
            def setUp(self):
                self.share_data(**{PARAMETER_NAME: PARAMETER_VALUE})

        # Block to check that the correct value is injected into the block
        ReadFromCommonBlock.READ_NAME = PARAMETER_NAME
        ReadFromCommonBlock.READ_VALUE = PARAMETER_VALUE

        FlowWithSetup.blocks = (ReadFromCommonBlock,)

        test_flow = FlowWithSetup()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.validate_blocks(test_flow, successes=1)

    def test_error_in_setup(self):
        """Create test flow with error in setUp and validate behavior.

        We test that the blocks were not run and that the result was error.
        """
        class FlowWithSetupError(MockFlow):
            def setUp(self):
                raise RuntimeError('Intentional error in setUp')

        FlowWithSetupError.blocks = (SuccessBlock,)

        test_flow = FlowWithSetupError()
        self.run_test(test_flow)

        self.assertFalse(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 1,
                         "Result didn't run the correct number of tests")

        self.assertEqual(len(self.result.errors), 1,
                         "Result didn't had the correct number of errors")

        self.validate_blocks(test_flow, successes=0)

        # === Validate data object ===
        self.assertFalse(test_flow.data.success,
                         'Flow data result should have been False')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.ERROR,
                        'Flow data status should have been error')

    def test_error_no_resources(self):
        """Validate that flows are skipped if they can't get the resources."""
        no_resource_name = 'no_such_resource'

        class TempFlow(MockFlow):
            resources = (request('no_resource',
                                 DemoResource,
                                 name=no_resource_name,
                                 dirty=False,),)

        TempFlow.blocks = (SuccessBlock,)

        test_flow = TempFlow()
        self.run_test(test_flow)

        # === Validate case data object ===
        self.assertEqual(test_flow.data.success, None,
                         'Flow data result should have been None')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.SKIPPED,
                        'Flow data status should have been skipped')

    def test_error_in_resources_locking(self):
        """Test TestFlow behavior on resource locking error.

        * Defines the registered resources as required resource.
        * Runs the test flow.
        * Validates that the test result is error.
        * Validates the flow's data object.
        * Validates the resources' state.
        """
        fail_resource_name = 'test_res2'

        class TempFlow(MockFlow):
            resources = (request('fail_resource',
                                 InitializeErrorResource,
                                 name=fail_resource_name,
                                 dirty=False,),)

        TempFlow.blocks = (SuccessBlock,)

        test_flow = TempFlow()
        self.run_test(test_flow)

        self.assertFalse(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.ERROR,
                        'Flow data status should have been error')

        # === Validate case data object ===
        self.assertFalse(test_flow.data.success,
                         'Flow data result should have been False')

        fail_resource = DemoResourceData.objects.get(name=fail_resource_name)

        self.validate_resource(fail_resource, dirty=True,
                               initialized=False, finalized=True)

    def test_error_in_teardown(self):
        """Validate test-flow behavior on tearDown error.

        We validate the blocks ran successfuly and the flow result was error.
        """
        class FlowWithTeardownError(MockFlow):
            def tearDown(self):
                raise RuntimeError('Intentional error in tearDown')

        FlowWithTeardownError.blocks = (SuccessBlock,)

        test_flow = FlowWithTeardownError()
        self.run_test(test_flow)

        self.assertFalse(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 1,
                         "Result didn't run the correct number of tests")

        self.assertEqual(len(self.result.errors), 1,
                         "Result didn't had the correct number of errors")

        self.validate_blocks(test_flow, successes=1)

        # === Validate data object ===
        self.assertFalse(test_flow.data.success,
                         'Flow data result should have been False')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.ERROR,
                        'Flow data status should have been error')

    def test_local_dynamic_resources_locking(self):
        """Test that cases can dynamically lock resources.

        * Runs a test that dynamically requests local resources.
        * Validates that the other blocks don't have the resources.
        * Validates that the resources were initialized and finalized.
        """
        global_resource_name = 'test_res1'

        dynamic_request_name = 'dynamic_resource'
        dynamic_resource_name = 'test_res2'

        class SharedDynamicResourceLockingBlock(DynamicResourceLockingBlock):
            is_global = False
            outputs = (dynamic_request_name,)
            dynamic_resources = (request(dynamic_request_name,
                                         DemoResource,
                                         name=dynamic_resource_name,
                                         dirty=False,),)

        AttributeCheckingBlock.ATTRIBUTE_NAME = dynamic_request_name

        MockFlow.blocks = (SharedDynamicResourceLockingBlock,
                           AttributeCheckingBlock)

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertFalse(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 1,
                         "Result didn't run the correct number of tests")

        self.assertEqual(len(self.result.failures), 1,
                         "Result didn't had the correct number of errors")

        self.validate_blocks(test_flow, successes=1, failures=1)

        # === Validate data object ===
        self.assertFalse(test_flow.data.success,
                         'Flow data result should have been False')

        test_resource = DemoResourceData.objects.get(name=global_resource_name)
        self.validate_resource(test_resource, dirty=False)
        test_resource = DemoResourceData.objects.get(
                                                 name=dynamic_resource_name)
        self.validate_resource(test_resource, dirty=False)

    def test_shared_dynamic_resources_locking(self):
        """Test that cases can dynamically lock resources.

        * Runs a test that dynamically requests shared resources.
        * Validates that the other blocks have the resources as well.
        * Validates that the resources were initialized and finalized.
        """
        global_resource_name = 'test_res1'

        dynamic_request_name = 'dynamic_resource'
        dynamic_resource_name = 'test_res2'

        class SharedDynamicResourceLockingBlock(DynamicResourceLockingBlock):
            is_global = True
            outputs = (dynamic_request_name,)
            dynamic_resources = (request(dynamic_request_name,
                                         DemoResource,
                                         name=dynamic_resource_name,
                                         dirty=False,),)

        AttributeCheckingBlock.ATTRIBUTE_NAME = dynamic_request_name

        MockFlow.blocks = (SharedDynamicResourceLockingBlock,
                           AttributeCheckingBlock)

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 1,
                         "Result didn't run the correct number of tests")

        self.validate_blocks(test_flow, successes=2)

        # === Validate data object ===
        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        test_resource = DemoResourceData.objects.get(name=global_resource_name)
        self.validate_resource(test_resource, dirty=False)
        test_resource = DemoResourceData.objects.get(
                                                 name=dynamic_resource_name)
        self.validate_resource(test_resource, dirty=False)

    def test_critical_blocks(self):
        """Validate behavior of block in CRITICAL mode.

        We check that other blocks don't run after a critical's failure.
        """
        MockFlow.blocks = (SuccessBlock.params(mode=MODE_CRITICAL),
                           FailureBlock.params(mode=MODE_CRITICAL),
                           SuccessBlock.params(mode=MODE_CRITICAL))

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertFalse(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 1,
                         "Result didn't run the correct number of tests")

        self.assertEqual(len(self.result.failures), 1,
                         "Result didn't fail the correct number of tests")

        self.validate_blocks(test_flow, successes=1, failures=1, skips=1)

        # === Validate data object ===
        self.assertFalse(test_flow.data.success,
                         'Flow data result should have been False')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.FAILED,
                        'Flow data status should have been failure')

    def test_optional_blocks(self):
        """Validate behavior of block in OPTIONAL mode.

        We check that other blocks run after a optional's failure but don't
        after an error in an optional block.
        """
        MockFlow.blocks = (SuccessBlock.params(mode=MODE_CRITICAL),
                           FailureBlock.params(mode=MODE_OPTIONAL),
                           SuccessBlock.params(mode=MODE_CRITICAL),
                           ErrorBlock.params(mode=MODE_OPTIONAL),
                           SuccessBlock.params(mode=MODE_CRITICAL))

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertFalse(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 1,
                         "Result didn't run the correct number of tests")

        self.assertEqual(len(self.result.errors), 1,
                         "Result didn't had the correct number of errors")

        self.validate_blocks(test_flow, successes=2, failures=1, errors=1,
                             skips=1)

        # === Validate data object ===
        self.assertFalse(test_flow.data.success,
                         'Flow data result should have been False')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.ERROR,
                        'Flow data status should have been error')

    def test_finally_blocks(self):
        """Validate behavior of block in FINALLY mode.

        We check that finally blocks run despite other's failure.
        """
        MockFlow.blocks = (SuccessBlock.params(mode=MODE_CRITICAL),
                           FailureBlock.params(mode=MODE_CRITICAL),
                           SuccessBlock.params(mode=MODE_FINALLY),
                           SuccessBlock.params(mode=MODE_CRITICAL),
                           SuccessBlock.params(mode=MODE_OPTIONAL))

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertFalse(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 1,
                         "Result didn't run the correct number of tests")

        self.assertEqual(len(self.result.failures), 1,
                         "Result didn't fail the correct number of tests")

        self.validate_blocks(test_flow, successes=2, failures=1, skips=2)

        # === Validate data object ===
        self.assertFalse(test_flow.data.success,
                         'Flow data result should have been False')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.FAILED,
                        'Flow data status should have been failure')

    def test_finally_failure_blocks(self):
        """Validate behavior of blocks after FINALLY block failure.

        We check that other blocks don't run after a finally's failure.
        """
        MockFlow.blocks = (SuccessBlock.params(mode=MODE_CRITICAL),
                           FailureBlock.params(mode=MODE_FINALLY),
                           SuccessBlock.params(mode=MODE_CRITICAL),
                           SuccessBlock.params(mode=MODE_OPTIONAL))

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertFalse(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 1,
                         "Result didn't run the correct number of tests")

        self.assertEqual(len(self.result.failures), 1,
                         "Result didn't fail the correct number of tests")

        self.validate_blocks(test_flow, successes=1, failures=1, skips=2)

        # === Validate data object ===
        self.assertFalse(test_flow.data.success,
                         'Flow data result should have been False')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.FAILED,
                        'Flow data status should have been failure')

    def test_sub_flow_inputs(self):
        """Test behavior of inputs validation of sub-flows in positive case.

        * First propagating parameter = resource from the upper flow's request.
        * Second propagating parameter = initial common data field.
        * Third propagating parameter = field injected to the sub-flow using
            'parametrize'.
        * The block validates it gets all three parameters.
        """
        FLOW_PARAMETER_NAME = 'some_parameter1'
        COMMON_PARAMETER_NAME = 'some_parameter2'

        FLOW_PARAMETER_VALUE = 'some_value1'
        COMMON_PARAMETER_VALUE = 'some_value2'

        class ResourceCheckingBlock(AttributeCheckingBlock):
            inputs = ('res1',)
            ATTRIBUTE_NAME = 'res1'

        class CommonCheckingBlock(AttributeCheckingBlock):
            inputs = (COMMON_PARAMETER_NAME,)
            ATTRIBUTE_NAME = COMMON_PARAMETER_NAME

        class ParametrizeCheckingBlock(AttributeCheckingBlock):
            inputs = (FLOW_PARAMETER_NAME,)
            ATTRIBUTE_NAME = FLOW_PARAMETER_NAME

        MockSubFlow.blocks = (ResourceCheckingBlock,
                              CommonCheckingBlock,
                              ParametrizeCheckingBlock)

        class MainFlow(MockFlow):
            blocks = (MockSubFlow,)

        # No flow parameter and no common parameter
        with self.assertRaises(AttributeError):
            MainFlow()

        # Adding initial common field
        MainFlow.common = {COMMON_PARAMETER_NAME: COMMON_PARAMETER_VALUE}

        # No flow parameter
        with self.assertRaises(AttributeError):
            MainFlow()

        # Parametrizing the sub-flow
        MainFlow.blocks = (MockSubFlow.params(**{FLOW_PARAMETER_NAME:
                                                 FLOW_PARAMETER_VALUE}),)

        # Got all fields needed
        test_flow = MainFlow()

        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.validate_blocks(test_flow, successes=1)

    def test_sub_flow_propagating_share(self):
        """Test behavior of the common object in sub-flow.

        * Check that fields shared in the upper flow are available to all.
        * Check that fields shared in sub-flow are not available in the top.
        """
        UPPER_FIELD_NAME = 'upper_field'
        UPPER_FIELD_VALUE = 'some_value1'

        SUB_FIELD_NAME = 'sub_field'
        SUB_FIELD_VALUE = 'some_value2'

        class UpperWritingBlock(WriteToCommonBlock):
            INJECT_NAME = UPPER_FIELD_NAME
            INJECT_VALUE = UPPER_FIELD_VALUE

        class SubWritingBlock(WriteToCommonBlock):
            INJECT_NAME = SUB_FIELD_NAME
            INJECT_VALUE = SUB_FIELD_VALUE

        class UpperCheckingBlock(AttributeCheckingBlock):
            ATTRIBUTE_NAME = UPPER_FIELD_NAME

        class SubCheckingBlock(AttributeCheckingBlock):
            ATTRIBUTE_NAME = SUB_FIELD_NAME

        class FailingSubCheckingBlock(MockBlock):
            ATTRIBUTE_NAME = SUB_FIELD_NAME

            def test_attr_doesnt_exists(self):
                self.assertFalse(hasattr(self, self.ATTRIBUTE_NAME))

        MockSubFlow.blocks = (FailingSubCheckingBlock,  # Not injected yet
                              UpperCheckingBlock,  # Injected from upper
                              SubWritingBlock,
                              SubCheckingBlock)

        class MainFlow(MockFlow):
            blocks = (UpperWritingBlock,
                      MockSubFlow,
                      FailingSubCheckingBlock)  # Not available in upper

        test_flow = MainFlow()
        self.run_test(test_flow)
        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.assertEqual(self.result.testsRun, 1,
                         "Result didn't run the correct number of tests")

        self.validate_blocks(test_flow, successes=3)

    def test_critical_flow(self):
        """Validate behavior of flow in CRITICAL mode.

        We check that other blocks don't run after a critical flow's failure.
        """
        MockSubFlow.blocks = (FailureBlock.params(mode=MODE_CRITICAL),)
        MockFlow.blocks = (SuccessBlock.params(mode=MODE_CRITICAL),
                           MockSubFlow.params(mode=MODE_CRITICAL),
                           SuccessBlock.params(mode=MODE_CRITICAL))

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertFalse(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 1,
                         "Result didn't run the correct number of tests")

        self.assertEqual(len(self.result.failures), 1,
                         "Result didn't fail the correct number of tests")

        self.validate_blocks(test_flow, successes=1, failures=1, skips=1)

        # === Validate data object ===
        self.assertFalse(test_flow.data.success,
                         'Flow data result should have been False')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.FAILED,
                        'Flow data status should have been failure')

    def test_optional_flow(self):
        """Validate behavior of flow in OPTIONAL mode.

        We check that other blocks run after a optional flow's failure but
        don't after an error in an optional flow.
        """
        MockSubFlow.blocks = (FailureBlock.params(mode=MODE_CRITICAL),)

        class ErrorSubFlow(MockSubFlow):
            blocks = (ErrorBlock.params(mode=MODE_CRITICAL),)

        MockFlow.blocks = (SuccessBlock.params(mode=MODE_CRITICAL),
                           FailureBlock.params(mode=MODE_OPTIONAL),
                           SuccessBlock.params(mode=MODE_CRITICAL),
                           ErrorSubFlow.params(mode=MODE_OPTIONAL),
                           SuccessBlock.params(mode=MODE_CRITICAL))

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertFalse(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 1,
                         "Result didn't run the correct number of tests")

        self.assertEqual(len(self.result.errors), 1,
                         "Result didn't had the correct number of errors")

        self.validate_blocks(test_flow, successes=2, failures=1, errors=1,
                             skips=1)

        # === Validate data object ===
        self.assertFalse(test_flow.data.success,
                         'Flow data result should have been False')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.ERROR,
                        'Flow data status should have been error')

    def test_finally_flow(self):
        """Validate behavior of flow in FINALLY mode.

        We check that finally flows run despite other's failure.
        """
        MockSubFlow.blocks = (SuccessBlock.params(mode=MODE_CRITICAL),)
        MockFlow.blocks = (SuccessBlock.params(mode=MODE_CRITICAL),
                           FailureBlock.params(mode=MODE_CRITICAL),
                           MockSubFlow.params(mode=MODE_FINALLY),
                           MockSubFlow.params(mode=MODE_CRITICAL),
                           MockSubFlow.params(mode=MODE_OPTIONAL))

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertFalse(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 1,
                         "Result didn't run the correct number of tests")

        self.assertEqual(len(self.result.failures), 1,
                         "Result didn't fail the correct number of tests")

        self.validate_blocks(test_flow, successes=2, failures=1, skips=2)

        # === Validate data object ===
        self.assertFalse(test_flow.data.success,
                         'Flow data result should have been False')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.FAILED,
                         'Flow data status should have been failure')


if __name__ == '__main__':
    django.setup()
    colored_main(defaultTest='TestTestFlow')
