"""Describes Rotest's basic test runner class."""
# pylint: disable=invalid-name,too-many-arguments
# pylint: disable=expression-not-assigned,no-member
# pylint: disable=too-many-instance-attributes,too-few-public-methods
from unittest.runner import TextTestRunner

from rotest.common import core_log
from rotest.core.case import TestCase
from rotest.core.suite import TestSuite
from rotest.core.result.result import Result
from rotest.core.models.run_data import RunData
from rotest.management.client.manager import ClientResourceManager


class AnonymousSuite(TestSuite):
    """Temporary TestSuite for running TestCases."""
    pass


class BaseTestRunner(TextTestRunner):
    """Handle Rotest's basic test runner.

    Attributes:
        result (Result): test run's result object.
        save_state (bool): determine if storing resources state is required.
            The behavior can be overridden using resource's save_state flag.
        skip_init (bool): True to skip resources initialization and validation.
        config (object): config object, will be transferred to each test.
        run_delta (bool): determine whether to run only tests that failed the
            last run (according to the results DB).
        outputs (list): list of the output handlers' names.
        run_name (str): name of the current run.
        enable_debug (bool): whether to enable entering ipdb debugging mode
            upon any exception in a test statement.
    """
    def __init__(self, save_state, config, run_delta, outputs,
                 run_name, enable_debug, skip_init=False, *args, **kwargs):
        """Initialize the tests runner.

        Sets the class members and gets Rotest's version as well as the
        given project's version from the database.
        """
        super(BaseTestRunner, self).__init__(*args, **kwargs)

        self.result = None
        self.test_item = None
        self.resource_manager = None

        self.config = config
        self.outputs = outputs
        self.run_name = run_name
        self.run_delta = run_delta
        self.skip_init = skip_init
        self.save_state = save_state
        self.enable_debug = enable_debug

    def _makeResult(self):
        """Create test result object.

        Returns:
            Result. test result object.
        """
        self.result = Result(stream=self.stream,
                             outputs=self.outputs,
                             main_test=self.test_item,
                             descriptions=self.descriptions)
        self.result.failfast = self.failfast

        return self.result

    @staticmethod
    def create_resource_manager():
        """Create a new resource manager client instance.

        Returns:
            ClientResourceManager. new resource manager client.
        """
        return ClientResourceManager(logger=core_log)

    def initialize(self, test_class):
        """Initialize the test runner.

        * Generates the test object for the given class.
        * Generates the test run data and links it to the test object.

        Args:
            test_class (type): test class inheriting from
                :class:`rotest.core.case.TestCase` or
                :class:`rotest.core.suite.TestSuite`.
        """
        core_log.debug('Generating run data for %r', self.run_name)
        run_data = RunData(run_name=self.run_name, run_delta=self.run_delta)

        core_log.debug("Creating resource client")
        self.resource_manager = self.create_resource_manager()

        core_log.debug('Creating test object for %r', test_class.get_name())
        self.test_item = test_class(
            run_data=run_data,
            config=self.config,
            skip_init=self.skip_init,
            save_state=self.save_state,
            enable_debug=self.enable_debug,
            resource_manager=self.resource_manager)

        run_data.main_test = self.test_item.data

    def finalize(self):
        """Finalize the test runner.

        * Removes duplicated test DB entries.
        """
        core_log.debug('Finalizing test %r', self.test_item.data.name)
        if self.resource_manager is not None:
            self.resource_manager.disconnect()

    def execute(self, test_item):
        """Execute the given test item.

        Args:
            test_item (object): TestSuite / TestCase object.

        Returns:
            RunData. test run data.
        """
        super(BaseTestRunner, self).run(test_item)

        return self.test_item.data.run_data

    def run(self, test_class):
        """Run the given test class.

        * Initializes the test runner.
        * Runs the tests and records its results.
        * Finalizes the test runner.

        Args:
            test_class (type): test class inheriting from
                :class:`rotest.core.case.TestCase` or
                :class:`rotest.core.suite.TestSuite`.

        Returns:
            rotest.core.models.run_data.RunData. test's run data.
        """
        if issubclass(test_class, TestCase):
            AnonymousSuite.components = (test_class,)
            test_class = AnonymousSuite

        test_name = test_class.get_name()

        core_log.debug('Initializing %r test runner', test_name)
        self.initialize(test_class)
        try:
            core_log.debug('Running test %r', test_name)
            return self.execute(self.test_item)

        finally:
            core_log.debug('Finalizing %r test runner', test_name)
            self.finalize()
