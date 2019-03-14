"""Describe TestBlock class."""
# pylint: disable=dangerous-default-value,too-many-arguments
from __future__ import absolute_import

from itertools import count

from future.utils import iteritems

from rotest.common.utils import get_class_fields
from rotest.common.config import ROTEST_WORK_DIR
from rotest.core.flow_component import (AbstractFlowComponent, MODE_OPTIONAL,
                                        MODE_FINALLY, MODE_CRITICAL,
                                        BlockInput, BlockOutput)

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

    Declaring 'inputs': assign class fields to instances of BlockInput to
    ask for values for the block (values are passed via common, parametrize,
    previous blocks passing them as outputs, or as requested resources).
    You can pass a default value to BlockInput to assign if non is supplied
    (making it an optional input).

    Declaring 'outputs': assign class fields to instances of BlockOutput to
    share values from the instance (self) to the parent and siblings.
    the block automatically shares the declared outputs after teardown.

    In case the blocks under a flow don't 'connect' properly (a block doesn't
    have its declared output in self.__dict__ or a block doesn't get all its
    inputs from) an error would be raised before the tests start.

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
        mode (number): running mode code. available modes are:
            CRITICAL: stop test flow on failure or error.
            FINALLY: always run this block, regardless of the others' result.
            OPTIONAL: don't stop test flow on failure (but do so on error),
                failure in this type of block still fails the test-flow.
        TAGS (list): list of tags by which the test may be filtered.
        IS_COMPLEX (bool): if this test is complex (may contain sub-tests).
    """
    IS_COMPLEX = False
    __test__ = False

    def __init__(self, indexer=count(), base_work_dir=ROTEST_WORK_DIR,
                 save_state=True, force_initialize=False, config=None,
                 parent=None, run_data=None, enable_debug=False,
                 resource_manager=None, skip_init=False, is_main=True):

        super(TestBlock, self).__init__(parent=parent,
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

        self.addCleanup(self._share_outputs)
        self._set_parameters(override_previous=False, **self.__class__.common)

    @classmethod
    def get_name(cls):
        """Return test name.

        You can override this class method and use values from 'common' to
        create a more indicative name for the test.

        Returns:
            str. test name.
        """
        class_name = cls.common.get(cls.COMPONENT_NAME_PARAMETER, cls.__name__)
        method_name = cls.get_test_method_name()
        return '.'.join((class_name, method_name))

    @classmethod
    def get_inputs(cls):
        """Return a dict of all the input instances of this block.

        Returns:
            dict. block's inputs (name: input placeholder instance).
        """
        return dict(get_class_fields(cls, BlockInput))

    @classmethod
    def get_outputs(cls):
        """Return a dict of all the input instances of this block.

        Returns:
            dict. block's inputs (name: input placeholder instance).
        """
        return dict(get_class_fields(cls, BlockOutput))

    def _share_outputs(self):
        """Share all the declared outputs of the block."""
        outputs_dict = {}
        for output_name in self.get_outputs():
            if output_name not in self.__dict__:
                self.logger.warning("Block %r didn't create output %r",
                                    self.data.name, output_name)

                continue

            if output_name in self._pipes:
                pipe = self._pipes[output_name]
                setattr(self, pipe.parameter_name, getattr(self, output_name))
                outputs_dict[pipe.parameter_name] = pipe.get_value(self)

            else:
                outputs_dict[output_name] = getattr(self, output_name)

        self.share_data(**outputs_dict)

    def validate_inputs(self, extra_inputs=[]):
        """Validate that all the required inputs of the blocks were passed.

        All names under the 'inputs' list must be attributes of the test-block
        when it begins to run, otherwise the block would raise an exception.

        Args:
            extra_inputs (list): fields the component would get from its parent
                or siblings.

        Raises:
            AttributeError: not all inputs were passed to the block.
        """
        required_inputs = [name
                           for (name, value) in iteritems(self.get_inputs())
                           if not value.is_optional()]

        for pipe_name, pipe in iteritems(self._pipes):
            if pipe_name in self.get_inputs():
                required_inputs.append(pipe.parameter_name)

        missing_inputs = [input_name for input_name in required_inputs
                          if (input_name not in self.__dict__ and
                              input_name not in extra_inputs and
                              input_name not in self._pipes)]

        if len(missing_inputs) > 0:
            raise AttributeError("Block %r under %r is missing mandatory "
                                 "inputs %s" %
                                 (self.data.name, self.parent, missing_inputs))
