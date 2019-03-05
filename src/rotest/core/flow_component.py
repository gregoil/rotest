"""Describe TestBlock class."""
# pylint: disable=attribute-defined-outside-init,unused-argument
# pylint: disable=too-many-arguments,too-many-locals,broad-except
# pylint: disable=dangerous-default-value,access-member-before-definition
# pylint: disable=bare-except,protected-access,too-many-instance-attributes
# pylint: disable=too-many-branches
from __future__ import absolute_import, print_function

import unittest
from functools import wraps
from itertools import count

from future.utils import iteritems
from future.builtins import range, object

from rotest.common import core_log
from rotest.common.utils import get_work_dir
from rotest.core.result.result import Result
from rotest.common.config import ROTEST_WORK_DIR
from rotest.core.abstract_test import AbstractTest
from rotest.management.common.errors import ServerError
from rotest.core.models.case_data import TestOutcome, CaseData


# CRITICAL: stop test on failure
# FINALLY: always run test, unskippable
# OPTIONAL: don't stop test on failure (but do so on error)
MODE_CRITICAL, MODE_FINALLY, MODE_OPTIONAL = range(1, 4)


class Pipe(object):
    """Used as reference to another parameter when using blocks and flows."""
    def __init__(self, parameter_name, formula=None):
        self.parameter_name = parameter_name
        self.formula = formula

    def get_value(self, block):
        """Extract the pointed value from the block.

        Args:
            block (AbstractFlowComponent): component to extract value from.

        Returns:
            object. pointed value.
        """
        value = getattr(block, self.parameter_name)
        if self.formula is not None:
            value = self.formula(value)

        return value


class BlockInput(object):
    """Used as declaration for an input for a block."""
    def __init__(self, default=NotImplemented):
        self.default = default

    def is_optional(self):
        """Return whether this input is optional or mandatory."""
        return self.default is not NotImplemented


class BlockOutput(object):
    """Used as declaration for an output for a block."""
    pass


class JumpException(KeyboardInterrupt):
    """An exception raised when the current scope should be skipped.

    Attributes:
        jump_target (AbstractFlowComponent): the component which's scope
            should run next.
    """
    def __init__(self, jump_target):
        super(JumpException, self).__init__()
        self.jump_target = jump_target


class AbstractFlowComponent(AbstractTest):
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
            (locked resources, values set via 'parametrize' or in 'share').
        outputs (tuple): lists the names of fields the block shares.
        mode (number): running mode code. available modes are:
            CRITICAL: stop test flow on failure or error.
            FINALLY: always run this block, regardless of the others' result.
            OPTIONAL: don't stop test flow on failure (but do so on error),
                failure in this type of block still fails the test-flow.
        TAGS (list): list of tags by which the test may be filtered.
        IS_COMPLEX (bool): if this test is complex (may contain sub-tests).
    """
    COMPONENT_NAME_PARAMETER = 'name'
    NO_RESOURCES_MESSAGE = 'Failed to request resources'
    PREVIOUS_FAILED_MESSAGE = 'Previous component failed'

    common = {}
    mode = MODE_CRITICAL

    def __init__(self, indexer=count(), base_work_dir=ROTEST_WORK_DIR,
                 save_state=True, force_initialize=False, config=None,
                 parent=None, run_data=None, enable_debug=False,
                 resource_manager=None, skip_init=False, is_main=True):

        test_method_name = self.get_test_method_name()
        super(AbstractFlowComponent, self).__init__(
                                        methodName=test_method_name,
                                        parent=parent,
                                        indexer=indexer,
                                        save_state=save_state,
                                        force_initialize=force_initialize,
                                        config=config,
                                        enable_debug=enable_debug,
                                        resource_manager=resource_manager,
                                        skip_init=skip_init)

        self._pipes = {}
        self.is_main = is_main

        name = self.get_name()
        core_log.debug("Initializing %r flow-component", name)

        core_log.debug("Creating database entry for %r test-block", name)
        self.work_dir = get_work_dir(base_work_dir, name, self)
        self.data = CaseData(name=name, run_data=run_data)

        if self.resource_manager is None:
            self.resource_manager = self.create_resource_manager()
            self._is_client_local = True

    @classmethod
    def parametrize(cls, **parameters):
        """Return a clone of this class with the given args in the common.

        Use this method (or its syntactic sugar 'params') to pass values to
        components under a flow.
        """
        new_common = cls.common.copy()
        new_common.update(**parameters)
        class_name = new_common.get('name', cls.__name__)
        return type(class_name, (cls,), {'common': new_common,
                                         '__doc__': cls.__doc__})

    # Shortcut
    params = parametrize

    def share_data(self, override_previous=True, **parameters):
        """Inject the parameters to the parent and sibling components.

        Args:
            override_previous (bool): whether to override previous value of
                the parameters if they were already injected or not.
        """
        if not self.IS_COMPLEX:
            self.parent._set_parameters(override_previous=override_previous,
                                        **parameters)

        else:
            self._set_parameters(override_previous=override_previous,
                                 **parameters)

    def get_short_errors(self):
        """Get short description of errors and failures.

        Yields:
            str. bottom line of all the errors.
        """
        if not self.was_successful():
            for traceback in self.data.traceback.split(
                        CaseData.TB_SEPARATOR):

                traceback = traceback.strip(" \n")
                bottom_line = traceback.rsplit("\n", 1)[-1].strip()
                yield "{}: {}".format(self.data.name, bottom_line)

    @classmethod
    def get_test_method_name(cls):
        """Return the test method name to run.

        Returns:
            str. test method name to run.
        """
        loader = unittest.loader.TestLoader()
        test_names = loader.getTestCaseNames(cls)

        if len(test_names) != 1:
            raise AttributeError("Component %r has illegal number of test "
                                 "methods : %s" % (cls.__name__, test_names))

        return test_names[0]

    def _decorate_setup(self, setup_method):
        """Decorate setUp method to handle skips, and resources requests.

        Args:
            setup_method (method): the original setUp method.

        Returns:
            method. the wrapped setUp method.
        """
        @wraps(setup_method)
        def setup_method_wrapper(*args, **kwargs):
            """setup method wrapper.

            * Locks the required resources for the test.
            * Executes the original setUp method.
            * Upon exception, finalizes the resources.
            """
            if self.is_main:
                if isinstance(self.result, Result):
                    skip_reason = self.result.shouldSkip(self)

                    if skip_reason is not None:
                        self.skip_sub_components(skip_reason)
                        self.skipTest(skip_reason)

            else:
                if self.mode in (MODE_CRITICAL, MODE_OPTIONAL):
                    siblings = list(self.parent)
                    for component in siblings:
                        if component is self:
                            break

                        if component.is_failing():
                            self.skip_sub_components(
                                                self.PREVIOUS_FAILED_MESSAGE)
                            self.skipTest(self.PREVIOUS_FAILED_MESSAGE)

            try:
                self.request_resources(self.get_resource_requests(),
                                       use_previous=True)

                self.override_resource_loggers()

            except Exception as err:
                if isinstance(err, ServerError):
                    self.skip_sub_components(self.NO_RESOURCES_MESSAGE)

                raise

            try:
                if not self.IS_COMPLEX:
                    self._set_parameters(override_previous=False,
                                         **{input_name: value.default
                                            for (input_name, value) in
                                            iteritems(self.get_inputs())
                                            if value.is_optional()})

                    for pipe_name, pipe in iteritems(self._pipes):
                        if pipe_name in self.get_inputs():
                            setattr(self, pipe_name, pipe.get_value(self))

                if not self.is_main:
                    # Validate all required inputs were passed
                    self.validate_inputs()

                setup_method(*args, **kwargs)
                if isinstance(self.result, Result):
                    self.result.setupFinished(self)

            except Exception:
                self.release_resources(self.locked_resources, dirty=True)
                raise

        return setup_method_wrapper

    def tearDown(self):
        """TearDown method."""
        pass

    def store_state(self):
        """Store the state of the resources in the work dir."""
        if self.is_main:
            super(AbstractFlowComponent, self).store_state()

    def run(self, result=None):
        """Run the test component.

        * Decorate setUp method to handle link skips, and resources requests.
        * Runs the original run method.

        Args:
            result (rotest.core.result.result.Result): test result information.
        """
        self.result = result
        self.create_logger()

        # === Decorate the setUp and tearDown methods ===
        setup_method = getattr(self, self.SETUP_METHOD_NAME)
        setattr(self, self.SETUP_METHOD_NAME,
                self._decorate_setup(setup_method))

        teardown_method = getattr(self, self.TEARDOWN_METHOD_NAME)
        setattr(self, self.TEARDOWN_METHOD_NAME,
                self._decorate_teardown(teardown_method))

        try:
            super(AbstractFlowComponent, self).run(result)

        except JumpException as e:
            self.data.exception_type = TestOutcome.SKIPPED
            if e.jump_target is not self.parent:
                raise

    def is_failing(self):
        """State if the component fails the flow (according to its mode).

        Returns:
            bool. True if the flow failed, False otherwise.
        """
        if self.data.exception_type is None:
            return False

        if self.mode in (MODE_CRITICAL, MODE_FINALLY) and \
                self.data.exception_type not in TestOutcome.POSITIVE_RESULTS:
            return True

        if self.mode in (MODE_OPTIONAL,) and \
                self.data.exception_type not in TestOutcome.UNCRITICAL_RESULTS:
            return True

        return False

    # override in subs

    def list_blocks(self, _):
        """Print the hierarchy down starting from the current component."""
        print(self.get_name())

    def was_successful(self):
        """Indicate whether or not the component was successful.

        Returns:
            bool. Whether of not the test was successful.
        """
        return self.data.exception_type is None or \
            self.data.exception_type in TestOutcome.POSITIVE_RESULTS

    def had_error(self):
        """Indicate whether or not the component contained an error.

        Returns:
            bool. Whether of not the component contains an error.
        """
        return self.data.exception_type == TestOutcome.ERROR

    @classmethod
    def get_name(cls):
        """Return test name.

        You can override this class method and use values from 'common' to
        create a more indicative name for the test.

        Returns:
            str. test name.
        """
        pass

    def skip_sub_components(self, reason):
        """Skip the sub-components of the test.

        Args:
            reason (str): skip reason to put.
        """
        pass

    def _set_parameters(self, override_previous=True, **parameters):
        """Inject parameters into the component.

        Args:
            override_previous (bool): whether to override previous value of
                the parameters if they were already injected or not.
        """
        for name, value in iteritems(parameters):
            if isinstance(value, Pipe):
                if override_previous or (name not in self.__dict__ and
                                         name not in self._pipes):

                    self._pipes[name] = value

            else:
                if override_previous or (name not in self.__dict__ and
                                         name not in self._pipes):

                    setattr(self, name, value)

    def validate_inputs(self, extra_inputs=[]):
        """Validate that all the required inputs of the component were passed.

        Args:
            extra_inputs (list): fields the component would get from its parent
                or previous siblings.

        Raises:
            AttributeError: not all inputs were passed to the component.
        """
        pass
