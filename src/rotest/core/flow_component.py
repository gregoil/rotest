"""Describe TestBlock class."""
# pylint: disable=attribute-defined-outside-init,unused-argument
# pylint: disable=too-many-arguments,too-many-locals,broad-except
# pylint: disable=dangerous-default-value,access-member-before-definition
# pylint: disable=bare-except,protected-access,too-many-instance-attributes
import sys
import unittest
from bdb import BdbQuit
from functools import wraps
from itertools import count

from ipdbugger import debug
from attrdict import AttrDict

from rotest.common import core_log
from rotest.common.utils import get_work_dir
from rotest.common.log import get_test_logger
from rotest.common.config import ROTEST_WORK_DIR
from rotest.management.common.errors import ServerError
from rotest.core.models.case_data import TestOutcome, CaseData
from rotest.management.client.manager import ClientResourceManager


# CRITICAL: stop test on failure
# FINALLY: always run test, unskippable
# OPTIONAL: don't stop test on failure (but do so on error)
MODE_CRITICAL, MODE_FINALLY, MODE_OPTIONAL = xrange(1, 4)


class PipeTo(object):
    """Used as reference to another parameter when using blocks and flows."""
    def __init__(self, parameter_name):
        self.parameter_name = parameter_name


class ClassInstantiator(object):
    """Container that holds instantiation parameters for a flow component."""
    def __init__(self, component_class, **parameters):
        self.component_class = component_class
        self.parameters = parameters

    def __call__(self, *args, **kwargs):
        """Instantiate the block with the parameters."""
        block = self.component_class(*args,
                                     parameters=self.parameters,
                                     **kwargs)

        block._set_parameters(**self.parameters)

        return block

    def get_name(self, **parameters):
        """Return test name.

        Args:
            method_name (str): name of the test method.

        Returns:
            str. test name.
        """
        parameters.update(self.parameters)
        return self.component_class.get_name(**parameters)


class AbstractFlowComponent(unittest.TestCase):
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
        force_validate (bool): a flag to determine if the resource will be
            validated once it requested (even if not marked as dirty).
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
    SETUP_METHOD_NAME = 'setUp'
    TEARDOWN_METHOD_NAME = 'tearDown'
    COMPONENT_NAME_PARAMETER = 'name'
    NO_RESOURCES_MESSAGE = 'Failed to request resources'
    PREVIOUS_FAILED_MESSAGE = 'Previous component failed'

    resources = ()
    mode = MODE_CRITICAL

    def __init__(self, indexer=count(), base_work_dir=ROTEST_WORK_DIR,
                 save_state=True, force_validate=False, config=None,
                 parent=None, run_data=None, enable_debug=True,
                 resource_manager=None, skip_init=False, is_main=True,
                 parameters={}):
        """Validate & initialize the TestBlock.

        Args:
            indexer (iterator): the generator of test indexes.
            base_work_dir (str): the base directory of the tests.
            save_state (bool): flag to determine if storing the states of
                resources is required.
            force_validate (bool): a flag to determine if the resource will be
                validated once it requested (even if not marked as dirty).
            config (AttrDict): dictionary of configurations.
            parent (TestCase): container of this test.
            run_data (RunData): test run data object.
            enable_debug (bool): whether to enable entering ipdb debugging mode
                upon any exception in a test statement.
            resource_manager (ClientResourceManager): tests' client resource
                manager instance, leave None to create a new one for the test.
            skip_init (bool): True to skip resources initialize and validation.
            is_main (bool): whether the instance is the root of the flow tree
                or is a sub-component of another flow.
            parameters (dict): parameters this component was instantiated with.

        Raises:
            AttributeError: in case of empty resource tuple.
        """
        test_method_name = self.get_test_method_name()
        if enable_debug is True:
            for method_name in (test_method_name, self.SETUP_METHOD_NAME,
                                self.TEARDOWN_METHOD_NAME):

                debug(getattr(self, method_name),
                      ignore_exceptions=[KeyboardInterrupt,
                                         unittest.SkipTest,
                                         BdbQuit])

        super(AbstractFlowComponent, self).__init__(test_method_name)

        self._pipes = {}
        self._tags = None
        self.result = None
        self.config = config
        self.parent = parent
        self.is_main = is_main
        self.skip_init = skip_init
        self.parameters = parameters
        self.save_state = save_state
        self.identifier = indexer.next()
        self.enable_debug = enable_debug
        self.force_validate = force_validate
        self.parents_count = self._get_parents_count()

        self.all_resources = AttrDict()
        self.locked_resources = AttrDict()

        name = self.get_name(**parameters)
        core_log.debug("Initializing %r flow-component", name)

        core_log.debug("Creating database entry for %r test-block", name)
        self.work_dir = get_work_dir(base_work_dir, name)
        self.data = CaseData(name=name, run_data=run_data)

        self.logger = get_test_logger(repr(self.data), self.work_dir)

        self._is_client_local = False
        self.resource_manager = resource_manager

        if self.resource_manager is None:
            self.resource_manager = self.create_resource_manager()
            self._is_client_local = True

    def __getattr__(self, name):
        """Try to get attribute from a pipe if it's not found in self."""
        if '_pipes' in self.__dict__ and name in self.__dict__['_pipes']:
            return getattr(self, self._pipes[name])

        raise AttributeError("'%s' object has no attribute '%s'" %
                             (self.__class__.__name__, name))

    def create_resource_manager(self):
        """Create a new resource manager client instance.

        Returns:
            ClientResourceManager. new resource manager client.
        """
        return ClientResourceManager(logger=self.logger)

    @classmethod
    def parametrize(cls, **parameters):
        """Return a class instantiator for this class with the given args.

        Use this method (or its syntactic sugar 'params') to pass values to
        components under a flow.

        Note:
            This class method does not instantiate the component, but states
            values be injected into it after it would be initialized.
        """
        return ClassInstantiator(cls, **parameters)

    # Shortcut
    params = parametrize

    def share_data(self, **parameters):
        """Inject the parameters to the parent and sibling components."""
        if self.IS_COMPLEX is False:
            self.parent._set_parameters(**parameters)

        else:
            self._set_parameters(**parameters)

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

    def request_resources(self, resources_to_request, use_previous=False,
                          is_global=False):
        """Lock the requested resources and prepare them for the test.

        Lock the required resources using the resource manager, then assign
        each resource to its requested name, and update the result of the
        chosen resources. This method can also be used to add resources to all
        the sibling blocks under the test-flow.

        Args:
            resources_to_request (list): list of resource requests to lock.
            use_previous (bool): whether to use previously locked resources and
                release the unused ones.
            is_global (bool): whether to inject the resources to the parent and
                sibling components or not.
        """
        if len(resources_to_request) == 0:
            # No resources to requested
            return

        if not self.resource_manager.is_connected():
            self.resource_manager.connect()

        requested_resources = self.resource_manager.request_resources(
                                        config=self.config,
                                        skip_init=self.skip_init,
                                        use_previous=use_previous,
                                        save_state=self.save_state,
                                        base_work_dir=self.work_dir,
                                        requests=resources_to_request,
                                        force_validate=self.force_validate)

        if is_global is True:
            self.parent.add_resources(requested_resources, from_block=self)
            self.parent.locked_resources.update(requested_resources)

            if self.result is not None:
                self.result.updateResources(self.parent)

        else:
            self.add_resources(requested_resources)
            self.locked_resources.update(requested_resources)

            if self.result is not None:
                self.result.updateResources(self)

    def release_resources(self, resources, dirty=False, force_release=True):
        """Release resources and mark them as 'dirty' or 'clean'.

        Args:
            resources (dict): resources to release.
            dirty (bool): dirty state to set to the resources.
            force_release (bool): whether to always release to resources
                or enable saving them for next tests.
        """
        if len(resources) == 0:
            # No resources were locked
            return

        self.resource_manager.release_resources(resources,
                                                dirty=dirty,
                                                force_release=force_release)

        # Remove the resources from the test's resource to avoid double release
        for key in resources.keys():
            self.locked_resources.pop(key, None)
            if self.is_main is False:
                self.parent.locked_resources.pop(key, None)

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
            if self.is_main is True:
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
                self.request_resources(self.resources, use_previous=True)

            except Exception as err:
                self.logger.exception("Got an error while getting resources")

                if isinstance(err, ServerError) is True:
                    self.skip_sub_components(self.NO_RESOURCES_MESSAGE)
                    self.skipTest(self.NO_RESOURCES_MESSAGE)

                else:
                    raise

            try:
                setup_method(*args, **kwargs)

            except:
                self.release_resources(self.locked_resources, dirty=True)
                raise

        return setup_method_wrapper

    def _decorate_teardown(self, teardown_method, result):
        """Decorate the tearDown method to handle resource release.

        Args:
            teardown_method (method): the original tearDown method.
            result (rotest.core.result.result.Result): test result information.

        Returns:
            method. the wrapped tearDown method.
        """
        @wraps(teardown_method)
        def teardown_method_wrapper(*args, **kwargs):
            """tearDown method wrapper.

            * Executes the original tearDown method.
            * Releases the test resources.
            """
            try:
                teardown_method(*args, **kwargs)

            except:
                result.addError(self, sys.exc_info())

            finally:
                self.release_resources(self.locked_resources,
                        dirty=self.data.exception_type == TestOutcome.ERROR,
                        force_release=True)

                if (self._is_client_local is True and
                        self.resource_manager.is_connected() is True):

                    self.resource_manager.disconnect()

        return teardown_method_wrapper

    def tearDown(self):
        """TearDown method."""
        pass

    def _get_parents_count(self):
        """Get the number of ancestors.

        Returns:
            number. number of ancestors.
        """
        if self.parent is None:
            return 0

        return self.parent.parents_count + 1

    def start(self):
        """Update the data that the test started."""
        self.data.start()

    def end(self, test_outcome, details=None):
        """Update the data that the test ended.

        Args:
            test_outcome (number): test outcome code (as defined in
                rotest.core.models.case_data.TestOutcome).
            details (str): details of the result (traceback/skip reason).
        """
        self.data.update_result(test_outcome, details)

    def run(self, result=None):
        """Run the test component.

        * Decorate setUp method to handle link skips, and resources requests.
        * Runs the original run method.

        Args:
            result (rotest.core.result.result.Result): test result information.
        """
        self.result = result

        # === Decorate the setUp and tearDown methods ===
        setup_method = getattr(self, self.SETUP_METHOD_NAME)
        setattr(self, self.SETUP_METHOD_NAME,
                self._decorate_setup(setup_method))

        teardown_method = getattr(self, self.TEARDOWN_METHOD_NAME)
        setattr(self, self.TEARDOWN_METHOD_NAME,
                self._decorate_teardown(teardown_method, result))

        super(AbstractFlowComponent, self).run(result)

    def is_failing(self):
        """State if the component fails the flow (according to its mode).

        Returns:
            bool. True if the flow failed, False otherwise.
        """
        if self.mode in (MODE_CRITICAL, MODE_FINALLY) and \
                self.data.exception_type not in TestOutcome.POSITIVE_RESULTS:
            return True

        elif self.mode in (MODE_OPTIONAL,) and \
                self.data.exception_type not in TestOutcome.UNCRITICAL_RESULTS:
            return True

        return False

    # override in subs

    @classmethod
    def get_name(cls, **parameters):
        """Return test name.

        This method gets instantiation arguments that are passed to the
        component via 'parametrize' call, and can be overridden to give unique
        names to components.

        Returns:
            str. test name.
        """
        pass

    def add_resources(self, resources, from_block=None):
        """Register the resources to the block and set them as its attributes.

        Args:
            resources (dict): dictionary of attributes name to resources
                instance to add to the blocks.
            from_block (TestBlock): block to start adding from, leave None
                to add to all the blocks.
        """
        self.all_resources.update(resources)
        for name, resource in resources.iteritems():
            setattr(self, name, resource)

    def skip_sub_components(self, reason):
        """Skip the sub-components of the test.

        Args:
            reason (str): skip reason to put.
        """
        pass

    def _set_parameters(self, **parameters):
        """Inject parameters into the component."""
        for name, value in parameters.iteritems():
            if isinstance(value, PipeTo):
                parameter_name = value.parameter_name
                self._pipes[name] = parameter_name

                if parameter_name not in self.inputs:
                    self.inputs = list(self.inputs) + [parameter_name]

            else:
                setattr(self, name, value)

    def _validate_inputs(self, extra_inputs=[]):
        """Validate that all the required inputs of the component were passed.

        Args:
            extra_inputs (list): fields the component would get from its parent
                or previous siblings.

        Raises:
            AttributeError: not all inputs were passed to the component.
        """
        pass
