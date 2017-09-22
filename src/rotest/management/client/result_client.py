"""Result manager client implementation.

The result client interracts with the remote server and updates it of all the
tests' events in real-time, so at the end of a run, the server's database could
tell what and when tests and tests containers were run (including their
hierarchial structure), what were their results and error descriptions, and
additional data about the run.
"""
from rotest.common import core_log
from rotest.management.common import messages
from rotest.common.config import RESOURCE_MANAGER_HOST
from rotest.management.client.client import AbstractClient
from rotest.management.common.resource_descriptor import ResourceDescriptor
from rotest.management.common.utils import (TEST_ID_KEY,
                                            TEST_NAME_KEY,
                                            TEST_SUBTESTS_KEY,
                                            TEST_CLASS_CODE_KEY)


class ClientResultManager(AbstractClient):
    """Client side result manager.

    Responsible for updating the server of test events and run data.
    """
    def __init__(self, host=None, logger=core_log):
        """Initialize the result client."""
        if host is None:
            host = RESOURCE_MANAGER_HOST

        super(ClientResultManager, self).__init__(logger=logger, host=host)

    @classmethod
    def _create_test_dict(cls, test_item):
        """Recursively create a dict representing the test's hierarchy.

        Args:
            test_item (TestCase / TestSuite): the top test.

        Returns:
            dict. a dictionary representing the tests tree.
        """
        test_dict = {TEST_ID_KEY: test_item.identifier,
                     TEST_NAME_KEY: test_item.data.name}

        test_dict[TEST_CLASS_CODE_KEY] = type(test_item.data)

        if test_item.IS_COMPLEX:
            subtests = [cls._create_test_dict(sub_test)
                        for sub_test in test_item]

            test_dict[TEST_SUBTESTS_KEY] = subtests

        return test_dict

    def start_test_run(self, main_test):
        """Inform the result server of the start of the run.

        Args:
            main_test (TestCase / TestSuite): main test container of the run.
        """
        tests_tree_dict = self._create_test_dict(main_test)
        run_data = {'run_name': main_test.data.run_data.run_name}
        msg = messages.StartTestRun(tests=tests_tree_dict,
                                    run_data=run_data)

        self._request(msg)

    def update_run_data(self, run_data):
        """Update the run data in the server.

        Args:
            run_data (RunData): the run data instance.
        """
        run_data_fields = run_data.get_fields()
        msg = messages.UpdateRunData(run_data=run_data_fields)

        self._request(msg)

    def add_result(self, test_item, result_code, info=None):
        """Update the result of the test item in the result server.

        Args:
            test_item (TestCase): the test to update its result.
            result_code (number): the code of the result (TestOutcome code).
            info (str): additional data about the test outcome.
        """
        msg = messages.AddResult(test_id=test_item.identifier,
                                 code=result_code,
                                 info=info)
        self._request(msg)

    def start_test(self, test_item):
        """Inform the result server of the beginning of a test.

        Args:
            test_item (rotest.core.case.TestCase): the test to update about.
        """
        msg = messages.StartTest(test_id=test_item.identifier)
        self._request(msg)

    def should_skip(self, test_item):
        """Check if the test passed in the last run according to results DB.

        Args:
            test_item (rotest.core.case.TestCase): the test to query about.

        Returns:
            bool. True if the test should be skipped, False otherwise.
        """
        msg = messages.ShouldSkip(test_id=test_item.identifier)
        reply_msg = self._request(msg)
        return reply_msg.should_skip is not None

    def stop_test(self, test_item):
        """Inform the result server of the end of a test.

        Args:
            test_item (rotest.core.case.TestCase): the test to update about.
        """
        msg = messages.StopTest(test_id=test_item.identifier)
        self._request(msg)

    def update_resources(self, test_item):
        """Inform the result server of locked resources of a test.

        Args:
            test_item (rotest.core.case.TestCase): the test to update about.
        """
        resources = []
        if test_item.locked_resources is not None:
            resources = [ResourceDescriptor(type(resource),
                                            name=resource.data.name).encode()
                         for resource in
                         test_item.locked_resources.itervalues()]

        msg = messages.UpdateResources(test_id=test_item.identifier,
                                       resources=resources)
        self._request(msg)

    def start_composite(self, test_item):
        """Inform the result server of the beginning of a composite test.

        Args:
            test_item (rotest.core.suite.TestSuite): the test to update about.
        """
        msg = messages.StartComposite(test_id=test_item.identifier)
        self._request(msg)

    def stop_composite(self, test_item):
        """Inform the result server of the end of a composite test.

        Args:
            test_item (rotest.core.suite.TestSuite): the test to update about.
        """
        msg = messages.StopComposite(test_id=test_item.identifier)
        self._request(msg)
