"""Define TestFlow composed of test blocks or other test flows."""
# pylint: disable=protected-access
# pylint: disable=dangerous-default-value,unused-variable,too-many-arguments
from itertools import count

from rotest.core.block import TestBlock
from rotest.common.config import ROTEST_WORK_DIR
from rotest.core.models.case_data import TestOutcome
from rotest.core.flow_component import (AbstractFlowComponent, MODE_CRITICAL,
                                        MODE_FINALLY, MODE_OPTIONAL,
                                        ClassInstantiator)

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
        force_validate (bool): a flag to determine if the resource will be
            validated once it requested (even if not marked as dirty).
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
    common = {}
    blocks = ()

    TAGS = []
    TIMEOUT = 1800  # 30 min
    IS_COMPLEX = True

    TEST_METHOD_NAME = "test_run_blocks"

    def __init__(self, base_work_dir=ROTEST_WORK_DIR, save_state=True,
                 force_validate=False, config=None, indexer=count(),
                 parent=None, run_data=None, enable_debug=False, is_main=True,
                 skip_init=False, resource_manager=None, parameters={}):
        """Validate and initialize the TestFlow blocks & data.

        Initializes the common object according to :meth:`create_common` and
        assigns it as 'common' attribute for the contained test blocks.

        Initializes the flow data object and connect it to the data object of
        the blocks under it.

        Args:
            base_work_dir (str): the base directory of the tests.
            save_state (bool): flag to determine if storing the states of
                resources is required.
            config (AttrDict): dictionary of configurations.
            indexer (iterator): the generator of test indexes.
            parent (TestSuite): container of this test.
            run_data (RunData): test run data object.
            force_validate (bool): a flag to determine if the resource will be
                validated once it requested (even if not marked as dirty).
            enable_debug (bool): whether to enable entering ipdb debugging mode
                upon any exception in a test statement.
            skip_init (bool): True to skip resources initialize and validation.
            resource_manager (ClientResourceManager): tests' client resource
                manager instance, leave None to create a new one for the test.
            parameters (dict): parameters this component was instantiated with.

        Raises:
            AttributeError: if stages tuple is empty.
            TypeError: in case stages tuple contains anything other then
                classes inheriting from :class:`rotest.core.stage.TestStage`.
        """
        super(TestFlow, self).__init__(parent=parent,
                                       config=config,
                                       indexer=indexer,
                                       is_main=is_main,
                                       run_data=run_data,
                                       skip_init=skip_init,
                                       parameters=parameters,
                                       save_state=save_state,
                                       enable_debug=enable_debug,
                                       base_work_dir=base_work_dir,
                                       resource_manager=resource_manager)

        if len(self.blocks) == 0:
            raise AttributeError("Blocks list can't be empty")

        self._tests = []
        if self.resource_manager is None:
            self._is_client_local = True
            self.resource_manager = self.create_resource_manager()

        for test_class in self.blocks:

            if not ((isinstance(test_class, type) and
                     issubclass(test_class, (TestBlock, TestFlow))) or
                    isinstance(test_class, ClassInstantiator)):

                raise TypeError("Blocks under TestFlow must be classes "
                                "inheriting from TestBlock or TestFlow, "
                                "got %r" % test_class)

            test_item = test_class(parent=self,
                                   config=config,
                                   is_main=False,
                                   indexer=indexer,
                                   run_data=run_data,
                                   skip_init=skip_init,
                                   save_state=save_state,
                                   enable_debug=enable_debug,
                                   base_work_dir=self.work_dir,
                                   resource_manager=self.resource_manager)

            self.logger.debug("Adding %r to tests", test_item)
            self._tests.append(test_item)

        self.share_data(**self.__class__.common)

        if self.is_main is True:
            self._validate_inputs()

        self.logger.debug("Initialized %r test-flow successfully", self.data)

    def __iter__(self):
        return iter(self._tests)

    def _validate_inputs(self, extra_inputs=[]):
        """Validate that all the required inputs of the blocks were passed.

        All names under the 'inputs' list must be attributes of the test-blocks
        when it begins to run, otherwise the blocks would raise an exception.

        Args:
            extra_inputs (list): fields the component would get from its parent
                or siblings.

        Raises:
            AttributeError: not all inputs were passed to the block.
        """
        fields = [request.name for request in self.resources]
        fields.extend(extra_inputs)
        for block in self:
            block._validate_inputs(fields)
            if isinstance(block, TestBlock):
                fields.extend(block.outputs)

    @classmethod
    def get_name(cls, **parameters):
        """Return test name.

        This method gets gets instantiation arguments that are passed to the
        block via 'parametrize' call, and can be overridden to give unique
        names to blocks.

        Returns:
            str. test name.
        """
        return parameters.get(cls.COMPONENT_NAME_PARAMETER, cls.__name__)

    def _set_parameters(self, **parameters):
        """Inject parameters into the component and sub-components."""
        # The 'mode' parameter is only relevant to the current hierarchy
        setattr(self, 'mode', parameters.pop('mode', self.mode))

        super(TestFlow, self)._set_parameters(**parameters)
        for block in self:
            block._set_parameters(**parameters)

    def skip_sub_components(self, reason):
        """Skip the sub-components of the test.

        Args:
            reason (str): skip reason to put.
        """
        for test in self:
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
        super(TestFlow, self).add_resources(resources, from_block=None)

        all_blocks = list(self)
        start_index = 0
        if from_block is not None:
            start_index = all_blocks.index(from_block)

        for block in all_blocks[start_index:]:
            block.add_resources(resources)

    def _was_successful(self):
        """Return whether the result of the flow-run was success or not."""
        return all((block.data.success is not False for block in self))

    def _has_errors(self):
        """Return whether any of the blocks had an exception during its run."""
        return any((block.data.exception_type == TestOutcome.ERROR
                    for block in self))

    def test_run_blocks(self):
        """Main test method, run the blocks under the test-flow."""
        for test in self:
            test(self.result)

        if self._has_errors() is True:
            raise FlowRunException("Some of the blocks had errors")

        if self._was_successful() is False:
            self.fail("Some of the blocks have failed")

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
        for block in self:
            block.result = result

        super(TestFlow, self).run(result)


def create_flow(blocks, name="AnonymousFlow", mode=MODE_CRITICAL, common={}):
    """Auxiliary function to create test flows on the spot."""
    return type(name, (TestFlow,), {'mode': mode,
                                    'common': common,
                                    'blocks': blocks})
