"""Describe TestBlock class."""
# pylint: disable=dangerous-default-value,too-many-arguments
from itertools import count

from rotest.common.config import ROTEST_WORK_DIR
from rotest.core.flow_component import (AbstractFlowComponent, MODE_CRITICAL,
                                        MODE_FINALLY, MODE_OPTIONAL)

assert MODE_FINALLY
assert MODE_CRITICAL
assert MODE_OPTIONAL


class TestBlock(AbstractFlowComponent):
    """Define TestBlock, which is a part of a test.

    Defines tests that are parts of a greater test. The block is dependent on
    the containing :class:`rotest.core.flow.TestFlow` to lock and pass
    resources to it.

    Test blocks can only be skipped because of test related issues
    (e.g. no resources, test-flow stopped due to failure, intentional skip)
    and can't be skipped on account of 'run_delta' (passed in previous runs),
    tags filtering, etc.

    In case the blocks under a flow don't 'connect' properly (a block doesn't
    get all its inputs from the previous, parametrize or the flow's resources)
    a warning would be displayed to the user. This check is done on a static
    level (i.e. before running any test).

    Test authors should subclass TestBlock for their own tests and override
    'inputs' tuple with the names of the fields required for the run of the
    block, and override 'mode' to state the type of the block.

    Attributes:
        resources (tuple): list of the required resources. each item is a
            tuple of (resource_name, resource type, parameters dictionary),
            you can use :func:`rotest.core..request` to create the tuple.
        identifier (number): unique id of the test.
        data (rotest.core.models._data.Data): contain information
            about a test  run.
        logger (logging.Logger): test logger.
        save_state (bool): a flag to determine if storing the states of
            resources is required.
        force_initialize (bool): a flag to determine if the resources will be
            initialized even if their validation succeeds.
        config (AttrDict): dictionary of configurations.
        enable_debug (bool): whether to enable entering ipdb debugging mode
            upon any exception in a test statement.
        resource_manager (ClientResourceManager): client resource manager.
        skip_init (bool): True to skip resources initialize and validation.

        inputs (tuple): lists the names of fields the block expecteds to have
            (locked resources, values set via 'parametrize' or 'share').
        outputs (tuple): lists the names of fields the block shares.
        mode (number): running mode code. available modes are:
            CRITICAL: stop test flow on failure or error.
            FINALLY: always run this block, regardless of the others' result.
            OPTIONAL: don't stop test flow on failure (but do so on error),
                failure in this type of block still fails the test-flow.
        TAGS (list): list of tags by which the test may be filtered.
        IS_COMPLEX (bool): if this test is complex (may contain sub-tests).
    """
    inputs = ()
    outputs = ()

    IS_COMPLEX = False

    def __init__(self, indexer=count(), base_work_dir=ROTEST_WORK_DIR,
                 save_state=True, force_initialize=False, config=None,
                 parent=None, run_data=None, enable_debug=True,
                 resource_manager=None, skip_init=False, is_main=True,
                 parameters={}):

        super(TestBlock, self).__init__(parent=parent,
                                        config=config,
                                        indexer=indexer,
                                        is_main=is_main,
                                        run_data=run_data,
                                        skip_init=skip_init,
                                        parameters=parameters,
                                        save_state=save_state,
                                        enable_debug=enable_debug,
                                        base_work_dir=base_work_dir,
                                        force_initialize=force_initialize,
                                        resource_manager=resource_manager)

    @classmethod
    def get_name(cls, **parameters):
        """Return test name.

        This method gets gets instantiation arguments that are passed to the
        block via 'parametrize' call, and can be overridden to give unique
        names to blocks.

        Returns:
            str. test name.
        """
        class_name = parameters.get(cls.COMPONENT_NAME_PARAMETER,
                                    cls.__name__)

        method_name = cls.get_test_method_name()
        return '.'.join((class_name, method_name))

    def _validate_inputs(self, extra_inputs=[]):
        """Validate that all the required inputs of the blocks were passed.

        All names under the 'inputs' list must be attributes of the test-block
        when it begins to run, otherwise the block would raise an exception.

        Args:
            extra_inputs (list): fields the component would get from its parent
                or siblings.

        Raises:
            AttributeError: not all inputs were passed to the block.
        """
        missing_inputs = [input_name for input_name in self.inputs
                          if (not hasattr(self, input_name) and
                              input_name not in extra_inputs and
                              input_name not in self._pipes)]

        if len(missing_inputs) > 0:
            raise AttributeError("Block %r under %r is missing mandatory "
                                 "inputs %s" %
                                 (self.data.name, self.parent, missing_inputs))
