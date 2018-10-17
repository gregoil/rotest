"""Define Rotest's TestSuite, composed from test suites or test cases."""
# pylint: disable=method-hidden,bad-super-call,too-many-arguments
from __future__ import absolute_import

import unittest
from itertools import count

from future.builtins import next

from rotest.common import core_log
from rotest.core.case import TestCase
from rotest.core.flow import TestFlow
from rotest.common.utils import get_work_dir
from rotest.common.config import ROTEST_WORK_DIR
from rotest.core.models.suite_data import SuiteData


class TestSuite(unittest.TestSuite):
    """Test composed from other test suites or test cases.

    Test suite is defined by a sequence of :class:`rotest.core.case.TestCase`
    or :class:`rotest.core.suite.TestSuite` that would run in a specific order.
    The suite is responsible for running the test items one after the other.

    Test authors should subclass TestCase for their own tests and override
    **components** tuple with the required test items.

    Attributes:
        components (tuple): List of test classes, subclasses of
            :class:`rotest.core.case.TestCase` or
            :class:`rotest.core.suite.TestSuite`.
        data (rotest.core.models.SuiteData): Contain information about
            a test suite run.
        TAGS (list): list of tags by which the test may be filtered.
        IS_COMPLEX (bool): if this test is complex (may contain sub-tests).
    """
    components = ()

    TAGS = []
    IS_COMPLEX = True

    _cleanup = False

    def __init__(self, base_work_dir=ROTEST_WORK_DIR, save_state=True,
                 config=None, indexer=count(), parent=None, run_data=None,
                 enable_debug=False, skip_init=False, resource_manager=None):
        """Initialize 'components' & add them to the suite.

        Validates & initializes the TestSuite components & data object.

        Args:
            base_work_dir (str): the base directory of the tests.
            save_state (bool): flag to determine if storing the states of
                resources is required.
            config (AttrDict): dictionary of configurations.
            indexer (iterator): the generator of test indexes.
            parent (TestSuite): container of this test.
            run_data (RunData): test run data object.
            enable_debug (bool): whether to enable entering ipdb debugging mode
                upon any exception in a test statement.
            skip_init (bool): True to skip resources initialization and
                validation of resources.
            resource_manager (ClientResourceManager): tests' client resource
                manager instance, leave None to create a new one for the test.

        Raises:
            AttributeError: if components tuple is empty.
            TypeError: in case components tuple contains anything other than
                classes inheriting from :class:`rotest.core.case.TestCase`,
                :class:`rotest.core.suite.TestSuite`.
        """
        super(TestSuite, self).__init__()

        self.parent = parent
        name = self.get_name()
        self.identifier = next(indexer)
        self.resource_manager = resource_manager
        self.parents_count = self._get_parents_count()
        self.config = config

        if parent is not None:
            parent.addTest(self)

        core_log.debug("Initializing %r test-suite", name)
        if len(self.components) == 0:
            raise AttributeError("%s: Components tuple can't be empty" % name)

        core_log.debug("Creating database entry for %r test-suite", name)
        self.work_dir = get_work_dir(base_work_dir, name, self)
        self.data = SuiteData(name=name, run_data=run_data)

        for test_component in self.components:

            if issubclass(test_component, TestCase):
                for method_name in test_component.load_test_method_names():
                    test_item = test_component(parent=self,
                                        config=config,
                                        indexer=indexer,
                                        run_data=run_data,
                                        skip_init=skip_init,
                                        save_state=save_state,
                                        methodName=method_name,
                                        enable_debug=enable_debug,
                                        base_work_dir=self.work_dir,
                                        resource_manager=resource_manager)

                    core_log.debug("Adding %r to %r", test_item, self.data)

            elif issubclass(test_component, TestFlow):
                test_item = test_component(parent=self,
                                           config=config,
                                           indexer=indexer,
                                           run_data=run_data,
                                           skip_init=skip_init,
                                           save_state=save_state,
                                           enable_debug=enable_debug,
                                           base_work_dir=self.work_dir,
                                           resource_manager=resource_manager)

                core_log.debug("Adding %r to %r", test_item, self.data)

            elif issubclass(test_component, TestSuite):
                test_item = test_component(parent=self,
                               config=config,
                               indexer=indexer,
                               run_data=run_data,
                               skip_init=skip_init,
                               save_state=save_state,
                               enable_debug=enable_debug,
                               base_work_dir=self.work_dir,
                               resource_manager=resource_manager)

                core_log.debug("Adding %r to %r", test_item, self.data)

            else:
                raise TypeError("Components under TestSuite must be classes "
                                "inheriting from TestCase or TestSuite, "
                                "got %r" % test_component)

        core_log.debug("Initialized %r test-suite successfully", self.data)

    @classmethod
    def get_name(cls):
        """Return test name as used in Django DB.

        Returns:
            str. test name as used in Django DB.
        """
        return cls.__name__

    def run(self, result, debug=False):
        """Run the tests under the suite and update its data object.

        * Notify the data object that the test suite started.
        * Call the test suite run method.
        * Notify the data object that the test suite ended & update its result.

        Args:
            result (rotest.core.result.result.Result): Holder for
                test result information.
            debug (bool): If suite, tests will be run without collecting errors
                in a TestResult.

        Returns:
            rotest.core.result.result.Result. holder for test result
                information.
        """
        result.startComposite(self)

        core_log.debug("Running %r test-suite", self.data)
        result = super(TestSuite, self).run(result, debug)

        result.stopComposite(self)

        return result

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
