"""Define TestFlow composed of test blocks or other test flows."""
# pylint: disable=protected-access,unused-argument
# pylint: disable=dangerous-default-value,unused-variable,too-many-arguments
from __future__ import absolute_import, print_function
import sys
from itertools import count

import six

from rotest.core.block import TestBlock
from rotest.common.config import ROTEST_WORK_DIR
from rotest.core.flow_component import (AbstractFlowComponent, MODE_CRITICAL,
                                        MODE_FINALLY, MODE_OPTIONAL,
                                        JumpException)

assert MODE_FINALLY
assert MODE_CRITICAL
assert MODE_OPTIONAL


class FlowRunException(Exception):
    """An error raised in the flow if some of its blocks had an error."""
    pass


class TestFlow(AbstractFlowComponent):
    """Define test flow, composed from a sequence of test blocks.

    The TestFlow is responsible for running the blocks one after the other, the
    relation between the blocks (flow of the test) will be defined via the
    'mode' value of each block (see :class:`TestBlock`).

    Test flow is able to request resources for its run via **resources** field,
    and all its resources will be passed to the blocks as well.

    To statically share initial data with the flow and it's components,
    override the static 'common' variable.

    Details about each flow run will be saved under
    :class:`rotest.core.models.case_data.CaseData`

    Test authors should subclass TestFlow for their own tests and override
    **blocks** tuple with the required test blocks, and **resources** tuple
    to state the test-flow's required resources. Blocks can also be injected
    with values using the 'parametrize' class method (see :class:`TestBlock`
    documentation for more information).

    Note:
        Blocks will run in the order in which they are defined in the
        `blocks` tuple.

    Attributes:
        save_state (bool): flag to determine if storing the states of
            resources is required.
        skip_init (bool): True to skip resources initialization and validation.
        config (AttrDict): dictionary of configurations.
        identifier (number): unique id of the test.
        parent (TestSuite): container of this test.
        run_data (RunData): test run data object.
        logger (logging.Logger): test logger.
        enable_debug (bool): whether to enable entering ipdb debugging mode
            upon any exception in a test statement.
        force_initialize (bool): a flag to determine if the resources will be
            initialized even if their validation succeeds.
        resource_manager (ClientResourceManager): client resource manager.
        work_dir (str): test directory, contains test data and sub-tests.
        data (CaseData): Contain information about the test flow run.

        resources (tuple): list of the required resources to lock ahead for the
            use of all the blocks. each item is a tuple of
            (resource_name, resource type, parameters dictionary),
            you can use :func:`rotest.core.stage.request` to create the tuple.
        blocks (tuple): List of :class:`rotest.core.block.TestBlock` classes.
        TAGS (list): list of tags by which the test may be filtered.
        IS_COMPLEX (bool): if this test is complex (may contain sub-tests).
        TIMEOUT (number): timeout for flow run, None means no timeout.
    """
    blocks = ()

    TAGS = []
    TIMEOUT = 1800  # 30 min
    IS_COMPLEX = True

    TEST_METHOD_NAME = "test_run_blocks"

    def __init__(self, methodName='test_method', indexer=count(),
                 base_work_dir=ROTEST_WORK_DIR, save_state=True,
                 force_initialize=False, config=None, parent=None,
                 run_data=None, enable_debug=False, is_main=True,
                 skip_init=False, resource_manager=None):

        self._tests = []
        self._run_index = 0  # Index of the next block to run
        super(TestFlow, self).__init__(parent=parent,
                                       config=config,
                                       indexer=indexer,
                                       is_main=is_main,
                                       run_data=run_data,
                                       skip_init=skip_init,
                                       save_state=save_state,
                                       enable_debug=enable_debug,
                                       base_work_dir=base_work_dir,
                                       force_initialize=force_initialize,
                                       resource_manager=resource_manager)

        if len(self.blocks) == 0:
            raise AttributeError("Blocks list can't be empty")

        for test_class in self.blocks:
            if not (isinstance(test_class, type) and
                    issubclass(test_class, (TestBlock, TestFlow))):

                raise TypeError("Blocks under TestFlow must be classes "
                                "inheriting from TestBlock or TestFlow, "
                                "got %r" % test_class)

            test_class(parent=self,
                       config=config,
                       is_main=False,
                       indexer=indexer,
                       run_data=run_data,
                       skip_init=skip_init,
                       save_state=save_state,
                       enable_debug=enable_debug,
                       base_work_dir=self.work_dir,
                       resource_manager=self.resource_manager)

        self._set_parameters(override_previous=False, **self.__class__.common)

        if self.is_main:
            self.validate_inputs()

    def __iter__(self):
        return iter(self._tests)

    def addTest(self, test_item):
        self._tests.append(test_item)

    def validate_inputs(self, extra_inputs=[]):
        """Validate that all the required inputs of the blocks were passed.

        All names under the 'inputs' list must be attributes of the test-blocks
        when it begins to run, otherwise the blocks would raise an exception.

        Args:
            extra_inputs (list): fields the component would get from its parent
                or siblings.

        Raises:
            AttributeError: not all inputs were passed to the block.
        """
        fields = [request.name for request in self.get_resource_requests()]
        fields.extend(extra_inputs)
        for block in self:
            block.validate_inputs(fields)
            if isinstance(block, TestBlock):
                for output in block.get_outputs().keys():
                    if output in block._pipes:
                        fields.append(block._pipes[output].parameter_name)

                    else:
                        fields.append(output)

    @classmethod
    def get_name(cls):
        """Return test name.

        You can override this class method and use values from 'common' to
        create a more indicative name for the test.

        Returns:
            str. test name.
        """
        return cls.common.get(cls.COMPONENT_NAME_PARAMETER, cls.__name__)

    def _set_parameters(self, override_previous=True, **parameters):
        """Inject parameters into the component and sub components.

        Args:
            override_previous (bool): whether to override previous value of
                the parameters if they were already injected or not.
        """
        # The 'mode' parameter is only relevant to the current hierarchy
        setattr(self, 'mode', parameters.pop('mode', self.mode))

        super(TestFlow, self)._set_parameters(override_previous,
                                              **parameters)

        for block in self:
            block._set_parameters(override_previous, **parameters)

    def skip_sub_components(self, reason):
        """Skip the sub-components of the test.

        Args:
            reason (str): skip reason to put.
        """
        for test in self:
            self.result.startTest(test)
            self.result.addSkip(test, reason)
            test.skip_sub_components(reason)

    def add_resources(self, resources, from_block=None):
        """Add the resources to the blocks of the flow.

        Args:
            resources (dict): dictionary of attributes name to resources
                instance to add to the blocks.
            from_block (TestBlock): block to start adding from, leave None
                to add to all the blocks.
        """
        super(TestFlow, self).add_resources(resources)

        all_blocks = list(self)
        start_index = 0
        if from_block is not None:
            start_index = all_blocks.index(from_block)

        for block in all_blocks[start_index:]:
            block.add_resources(resources)

    def list_blocks(self, indent=0):
        """Print the hierarchy down starting from the current component.

        It also prints blocks indexes and the next block to run.

        Args:
            indent (number): recursion counter, to help print sub-flows better.
        """
        super(TestFlow, self).list_blocks(indent)
        for index, block in enumerate(self):
            print("    " * indent, end='')
            if index == self._run_index - 1:
                print(" ->", index, '- ', end='')

            else:
                print("   ", index, '- ', end='')

            block.list_blocks(index + 1)

    def jump_to(self, index):
        """Immediately jump to the start of the block at the given index.

        Args:
            index (number): block index to run.
        """
        self._run_index = index

        tracer = sys.gettrace()
        if tracer:
            debugger = six.get_method_self(tracer)

            def raise_jump(*_args):
                raise JumpException(self)

            debugger.postcmd = lambda *args: True
            debugger.do_continue(None)
            sys.settrace(raise_jump)

        else:
            raise JumpException(self)

    def was_successful(self):
        """Return whether the result of the flow-run was success or not."""
        return (all(block.was_successful() for block in self) and
                super(TestFlow, self).was_successful())

    def had_error(self):
        """Return whether any of the blocks had an exception during its run."""
        return (any(block.had_error() for block in self) or
                super(TestFlow, self).had_error())

    def test_run_blocks(self):
        """Main test method, run the blocks under the test-flow."""
        self._run_index = 0
        while self._run_index < len(self._tests):
            test = self._tests[self._run_index]
            self._run_index += 1
            test(self.result)

        all_issues = []

        for block in self:
            all_issues.extend(block.get_short_errors())

        if self.had_error():
            flow_result = 'The flow ended in error:\n  ' \
                          '{}'.format('\n  '.join(all_issues))

            failure = AssertionError(flow_result)
            self.result.addError(self, (failure.__class__, failure, None))
            return

        if not self.was_successful():
            flow_result = 'The flow ended in failure:\n  ' \
                          '{}'.format('\n  '.join(all_issues))

            failure = AssertionError(flow_result)
            self.result.addFailure(self, (failure.__class__, failure, None))
            return

    def run(self, result=None):
        """Run the test case.

        * Decorates setUp method to handle skips, and resources requests.
        * Decorates the tearDown method to handle resource release.
        * Runs the original run method.

        Args:
            result (rotest.core.result.result.Result): test result information.
        """
        # We set the result default value as None because of the overridden
        # method signature, but the Rotest test case does not support it.
        self._set_parameters(result=result)

        super(TestFlow, self).run(result)


def create_flow(blocks, name="AnonymousFlow", mode=MODE_CRITICAL, common={}):
    """Auxiliary function to create test flows on the spot."""
    return type(name, (TestFlow,), {'mode': mode,
                                    'common': common,
                                    'blocks': blocks})
