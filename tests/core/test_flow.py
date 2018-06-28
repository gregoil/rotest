"""Test TestSuite behavior and common variables."""
# pylint: disable=no-init,old-style-class,too-many-public-methods
# pylint: disable=too-many-lines,too-many-arguments,too-many-locals
from rotest.core.case import request
from rotest.core.models.case_data import TestOutcome
from rotest.core.flow_component import PipeTo, BlockInput, BlockOutput
from rotest.core.block import MODE_CRITICAL, MODE_FINALLY, MODE_OPTIONAL
from rotest.management.models.ut_models import (DemoResource,
                                                DemoResourceData,
                                                InitializeErrorResource)

from tests.core.utils import (FailureBlock, ErrorBlock, MockFlow,
                              SkipBlock, ExpectedFailureBlock,
                              UnexpectedSuccessBlock, NoMethodsBlock,
                              SuccessBlock, MultipleMethodsBlock,
                              BasicRotestUnitTest, MockSubFlow,
                              AttributeCheckingBlock, MockBlock,
                              DynamicResourceLockingBlock, StoreFailuresBlock,
                              create_reader_block, create_writer_block)


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
        MockFlow.blocks = (create_writer_block(inject_value='some_value'),
                           create_reader_block(inject_value='some_value'))

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.validate_blocks(test_flow, successes=2)

    def test_input_default_value(self):
        """Test that blocks' inputs' default value is injected by default."""
        MockFlow.blocks = (create_reader_block(inject_value='default_value',
                                               default='default_value'), )

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.validate_blocks(test_flow, successes=1)

    def test_shared_data_priority(self):
        """Test that shared data has higher priority than default values."""
        MockFlow.blocks = (create_writer_block(inject_value='some_value'),
                           create_reader_block(inject_value='some_value',
                                               default='default_value'))

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.validate_blocks(test_flow, successes=2)

    def test_common(self):
        """Check that test-flows' initial common data is injected at start."""
        parameter_value = 'some_value2'
        parameter_name = 'some_parameter2'

        class FlowWithCommon(MockFlow):
            common = {parameter_name: parameter_value}

        FlowWithCommon.blocks = (create_reader_block(
                                        inject_name=parameter_name,
                                        inject_value=parameter_value), )

        test_flow = FlowWithCommon()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.validate_blocks(test_flow, successes=1)

    def test_inputs_static_check(self):
        """Test static check of inputs validation of blocks.

        Run a flow with a block that expects an input it doesn't get,
        then expect it to have an error.
        """
        MockFlow.blocks = (create_reader_block(inject_name="missing_input",
                                               inject_value=5), )

        with self.assertRaises(AttributeError):
            MockFlow()

    def test_optional_inputs_static_check(self):
        """Test static check of optional inputs validation of blocks.

        Run a flow with a block that has an optional input,
        then expect it to succeed.
        """
        MockFlow.blocks = (create_reader_block(inject_name="missing_input",
                                               inject_value=4,
                                               default=5), )
        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertFalse(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.validate_blocks(test_flow, failures=1)

    def test_inputs_check(self):
        """Test runtime validation of inputs of blocks.

        Run a flow with a block that pretends to share data and a block that
        needs this data as an input.
        """
        class PretendToShareDataBlock(SuccessBlock):
            pretend_output = BlockOutput()

        MockFlow.blocks = (PretendToShareDataBlock,
                           create_reader_block(inject_name='pretend_output').
                           params(mode=MODE_FINALLY))
        test_flow = MockFlow()

        self.run_test(test_flow)
        self.assertFalse(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.validate_blocks(test_flow, successes=1, failures=1)

    def test_inputs_static_check_with_pipe(self):
        """Test static check of inputs validation of blocks when using pipes.

        Run a flow with a block that expects an piped input it doesn't get,
        then expect it to have an error.
        """
        class BlockWithInputs(SuccessBlock):
            noinput = BlockInput()

        MockFlow.blocks = (BlockWithInputs.params(
            noinput=PipeTo('pipe_target')), )

        with self.assertRaises(AttributeError):
            MockFlow()

    def test_parametrize(self):
        """Validate parametrize behavior.

        * Checks that passing values via parametrize passes the 'inputs' check.
        * Checks that the values set via parametrize are correct.
        * Checks that passing values via parametrize is local to the block.
        """
        parameter_value = 'some_value'
        parameter_name = 'some_parameter'
        parameters = {parameter_name: parameter_value}

        MockFlow.blocks = (create_reader_block(
                    inject_name=parameter_name,
                    inject_value=parameter_value).params(**parameters), )

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.validate_blocks(test_flow, successes=1)

    def test_pipes_happy_flow(self):
        """Validate parametrize behavior when using pipes."""
        MockFlow.blocks = (
            create_writer_block(inject_name='some_name'),
            create_reader_block(inject_name='pipe_target').params(
                pipe_target=PipeTo('some_name')))

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.validate_blocks(test_flow, successes=2)

    def test_pipes_in_common(self):
        """Validate parametrize behavior when using pipes in common."""
        ReadingBlock = create_reader_block(inject_name='pipe_target',
                                           inject_value=5)
        # The params is just so the input validation can find the piped field
        WritingBlock = create_writer_block(inject_name='some_name',
                                           inject_value=5).params(some_name=3)

        class FlowWithCommon(MockFlow):
            common = {'pipe_target': PipeTo('some_name')}

            blocks = (WritingBlock,
                      ReadingBlock)

        test_flow = FlowWithCommon()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.validate_blocks(test_flow, successes=2)

    def test_pipes_priority_over_common(self):
        """Validate pipes priority in params is higher than common values."""
        class FlowWithCommon(MockFlow):
            common = {'pipe_target': 'wrong_value'}

            blocks = (create_writer_block(inject_name='some_name'),
                      create_reader_block(inject_name='pipe_target').params(
                          pipe_target=PipeTo('some_name')))

        test_flow = FlowWithCommon()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.validate_blocks(test_flow, successes=2)

    def test_pipes_override(self):
        """Validate pipes priority in common is lower than params values."""
        class FlowWithCommon(MockFlow):
            common = {'pipe_target': PipeTo('wrong_field')}

            blocks = (create_writer_block(inject_name='wrong_field',
                                          inject_value='wrong_value').params(
                        wrong_field='wrong_value'),  # To pass input validation
                      create_writer_block(inject_name='some_name',
                                          inject_value='some_value'),
                      create_reader_block(inject_name='pipe_target',
                                          inject_value='some_value').params(
                          pipe_target='some_value'))

        test_flow = FlowWithCommon()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.validate_blocks(test_flow, successes=3)

    def test_setup_flow(self):
        """Check that test-flows' setUp method is called before the blocks."""
        parameter_value = 'some_value'
        parameter_name = 'some_parameter'

        class FlowWithSetup(MockFlow):
            def setUp(self):
                self.share_data(**{parameter_name: parameter_value})

        FlowWithSetup.blocks = (create_reader_block(
                                            inject_name=parameter_name,
                                            inject_value=parameter_value,
                                            default='wrong_value'),)

        test_flow = FlowWithSetup()
        self.run_test(test_flow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.validate_blocks(test_flow, successes=1)

    def test_flow_expect_failure(self):
        """Validate behavior of test flow with blocks that fail with 'expect'.

        We test the flow treats 'expect' failures like normal failures.
        """
        MockFlow.blocks = (StoreFailuresBlock.params(mode=MODE_CRITICAL),
                           SuccessBlock.params(mode=MODE_CRITICAL),
                           StoreFailuresBlock.params(mode=MODE_FINALLY))

        test_flow = MockFlow()
        self.run_test(test_flow)

        self.assertFalse(self.result.wasSuccessful(),
                         'Flow succeeded when it should have failed')

        self.assertEqual(self.result.testsRun, 1,
                         "Result didn't run the correct number of tests")

        self.assertEqual(len(self.result.failures), 1,
                         "Result didn't had the correct number of failures")

        self.validate_blocks(test_flow, skips=1, failures=2)

        # === Validate data object ===
        self.assertFalse(test_flow.data.success,
                         'Flow data result should have been False')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.FAILED,
                         'Flow data status should have been failure')

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
                                 name=no_resource_name),)

        TempFlow.blocks = (SuccessBlock,)

        test_flow = TempFlow()
        self.run_test(test_flow)

        # === Validate case data object ===
        self.assertEqual(test_flow.data.success, False,
                         'Flow data result should have been None')

        self.assertEqual(test_flow.data.exception_type, TestOutcome.ERROR,
                         'Flow data status should have been error')

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
                                 name=fail_resource_name),)

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

        self.validate_resource(fail_resource,
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
                                         name=dynamic_resource_name),)

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
        self.validate_resource(test_resource)
        test_resource = DemoResourceData.objects.get(
                                                 name=dynamic_resource_name)
        self.validate_resource(test_resource)

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
                                         name=dynamic_resource_name),)

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
        self.validate_resource(test_resource)
        test_resource = DemoResourceData.objects.get(
                                                 name=dynamic_resource_name)
        self.validate_resource(test_resource)

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
            res1 = BlockInput()
            ATTRIBUTE_NAME = 'res1'

        class CommonCheckingBlock(AttributeCheckingBlock):
            ATTRIBUTE_NAME = COMMON_PARAMETER_NAME

        setattr(CommonCheckingBlock, COMMON_PARAMETER_NAME, BlockInput())

        class ParametrizeCheckingBlock(AttributeCheckingBlock):
            ATTRIBUTE_NAME = FLOW_PARAMETER_NAME

        setattr(ParametrizeCheckingBlock, FLOW_PARAMETER_NAME, BlockInput())

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
        upper_field_name = 'upper_field'
        upper_field_value = 'some_value1'

        sub_field_name = 'sub_field'
        sub_field_value = 'some_value2'

        UpperWritingBlock = create_writer_block(inject_name=upper_field_name,
                                                inject_value=upper_field_value)

        SubWritingBlock = create_writer_block(inject_name=sub_field_name,
                                              inject_value=sub_field_value)

        class UpperCheckingBlock(AttributeCheckingBlock):
            ATTRIBUTE_NAME = upper_field_name

        class SubCheckingBlock(AttributeCheckingBlock):
            ATTRIBUTE_NAME = sub_field_name

        class FailingSubCheckingBlock(MockBlock):
            ATTRIBUTE_NAME = sub_field_name

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

    def test_parameters_priority(self):
        """Test priorities behavior of the common object and parameters.

        * Values passed from the parent are always stronger.
        * In the same level - parameterizing block is higher priority.
        * In the same level - Common values are the weakest.
        """
        parameter1_name = 'field1'
        parameter1_topflow_value = 'value_good'
        parameter1_subflow_value = 'value_bad1'
        parameter1_common_value = 'value_bad2'

        parameter2_name = 'field2'
        parameter2_subflow_value = 'value_good'
        parameter2_common_value = 'value_bad1'

        CheckingParameter1Block = create_reader_block(
            inject_name=parameter1_name,
            inject_value=parameter1_subflow_value)

        CheckingParameter2Block = create_reader_block(
            inject_name=parameter2_name,
            inject_value=parameter2_subflow_value)

        class SubFlow(MockSubFlow):
            common = {parameter1_name: parameter1_common_value,
                      parameter2_name: parameter2_common_value}

            blocks = (CheckingParameter1Block.parametrize(
                            **{parameter1_name: parameter1_subflow_value}),
                      CheckingParameter2Block.parametrize(
                            **{parameter2_name: parameter2_subflow_value}))

        class MainFlow(MockFlow):
            blocks = (SubFlow.parametrize(
                            **{parameter1_name: parameter1_topflow_value}),)

        test_flow = MainFlow()
        self.run_test(test_flow)
        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.assertEqual(self.result.testsRun, 1,
                         "Result didn't run the correct number of tests")

    def test_default_inputs_priority(self):
        """Test that the priority of default inputs values are lowest."""
        parameter1_name = 'field1'
        parameter2_name = 'field2'

        class FlowWithCommon(MockSubFlow):
            common = {parameter1_name: "common_value"}

            blocks = (create_reader_block(inject_name=parameter1_name,
                                          inject_value="common_value",
                                          default="default_value"),
                      create_reader_block(inject_name=parameter2_name,
                                          inject_value="params_value",
                                          default="default_value").params(
                          **{parameter2_name: "params_value"}))

        test_flow = FlowWithCommon()
        self.run_test(test_flow)
        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        self.validate_blocks(test_flow, successes=2)

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
