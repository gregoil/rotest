"""Describe resource oriented TestCases."""
# pylint: disable=too-many-public-methods,too-many-arguments
# pylint: disable=too-many-instance-attributes,too-few-public-methods
# pylint: disable=no-member,method-hidden,broad-except,bare-except,invalid-name
from __future__ import absolute_import
import unittest
from functools import wraps
from itertools import count

from rotest.common import core_log
from rotest.common.utils import get_work_dir
from rotest.common.config import ROTEST_WORK_DIR
from rotest.core.models.case_data import CaseData
from rotest.core.abstract_test import AbstractTest, request


assert request


class TestCase(AbstractTest):
    """Resource oriented :class:`unittest.TestCase`.

    Defines tests that interact with specific resources. The case is
    responsible for locking the required resources before running tests and
    releasing the resources after running all tests in the class using
    :class:`rotest.management.client.manager.ClientResourceManager`.

    Test authors should subclass TestCase for their own tests and override
    'resources' tuple with the required resource descriptors.

    Attributes:
        resources (tuple): list of the required resources. each item is a
            tuple of (resource_name, resource type, parameters dictionary),
            you can use :func:`rotest.core.case.request` to create the tuple.
        data (rotest.core.models.case_data.CaseData): contain information
            about a test case run.
        logger (logging.Logger): test logger.
        identifier (number): unique id of the test.
        work_dir (str): test directory, contains test data and sub-tests.
        save_state (bool): a flag to determine if storing the states of
            resources is required.
        force_initialize (bool): a flag to determine if the resources will be
            initialized even if their validation succeeds.
        config (AttrDict): dictionary of configurations.
        enable_debug (bool): whether to enable entering ipdb debugging mode
            upon any exception in a test statement.
        resource_manager (ClientResourceManager): client resource manager.
        skip_init (bool): True to skip resources initialize and validation.

        TAGS (list): list of tags by which the test may be filtered.
        TIMEOUT (number): timeout for case run, None means no timeout.
        IS_COMPLEX (bool): if this test is complex (may contain sub-tests).
    """
    IS_COMPLEX = False
    test_methods_names = None

    def __init__(self, indexer=count(), methodName='runTest',
                 base_work_dir=ROTEST_WORK_DIR, save_state=True,
                 force_initialize=False, config=None, parent=None,
                 run_data=None, enable_debug=True, resource_manager=None,
                 skip_init=False):

        super(TestCase, self).__init__(indexer, methodName, save_state,
                                       force_initialize, config, parent,
                                       enable_debug, resource_manager,
                                       skip_init)

        self.skip_reason = None
        self.skip_determined = False

        name = self.get_name(methodName)
        core_log.debug("Initializing %r test-case", name)

        core_log.debug("Creating database entry for %r test-case", name)
        self.work_dir = get_work_dir(base_work_dir, name, self)
        self.data = CaseData(name=name, run_data=run_data)

        core_log.debug("Initialized %r test-case successfully", name)

        if self.resource_manager is None:
            self.resource_manager = self.create_resource_manager()
            self._is_client_local = True

    @classmethod
    def get_name(cls, method_name):
        """Return test name.

        Returns:
            str. test name.
        """
        return '.'.join((cls.__name__, method_name))

    @classmethod
    def load_test_method_names(cls):
        """Return all test method names to run.

        Returns:
            list. all test method names to run.
        """
        if cls.test_methods_names is None:
            loader = unittest.loader.TestLoader()
            return loader.getTestCaseNames(cls)

        return cls.test_methods_names

    def _decorate_setup(self, setup_method):
        """Decorate setUp method to handle link skips, and resources requests.

        Args:
            setup_method (function): the original setUp method.

        Returns:
            function. the wrapped setUp method.
        """
        @wraps(setup_method)
        def setup_method_wrapper(*args, **kwargs):
            """setup method wrapper.

            * Locks the required resources for the test.
            * Executes the original setUp method.
            * Upon exception, finalizes the resources.
            """
            skip_reason = self.result.shouldSkip(self)
            if skip_reason is not None:
                self.skipTest(skip_reason)

            self.request_resources(self.get_resource_requests(),
                                   use_previous=True)

            try:
                setup_method(*args, **kwargs)
                self.result.setupFinished(self)

            except Exception:
                self.release_resources(dirty=True)
                raise

        return setup_method_wrapper

    def run(self, result=None):
        """Run the test case.

        * Decorate setUp method to handle link skips, and resources requests.
        * Decorate the tearDown method to handle resource release.
        * Runs the original run method.

        Args:
            result (rotest.core.result.result.Result): test result information.
        """
        # We set the result default value as None because of the overridden
        # method signature, but the Rotest test case does not support it.
        self.assertIsNotNone(result, 'TestCase must run inside a TestSuite')
        self.result = result

        # === Decorate the setUp, test and tearDown methods. ===
        setup_method = getattr(self, self.SETUP_METHOD_NAME)
        setattr(self, self.SETUP_METHOD_NAME,
                self._decorate_setup(setup_method))

        teardown_method = getattr(self, self.TEARDOWN_METHOD_NAME)
        setattr(self, self.TEARDOWN_METHOD_NAME,
                self._decorate_teardown(teardown_method, result))

        super(TestCase, self).run(result)
