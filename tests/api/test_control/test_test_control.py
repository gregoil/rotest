"""Basic unittests for the server test control operations."""
# pylint: disable=protected-access
from __future__ import absolute_import

from functools import partial

from future.builtins import next
from six.moves import http_client
from django.test import Client, TransactionTestCase

from rotest.core.models import RunData
from rotest.core.models.case_data import TestOutcome
from rotest.management.client.result_client import ClientResultManager

from tests.api.utils import request
from tests.core.utils import (MockSuite1,
                              MockSuite2,
                              MockTestSuite,
                              MockCase,
                              MockCase1, MockCase2, SuccessCase)


class TestControl(TransactionTestCase):
    """Very basic unittests for asserting server responses.

    Note:
        more in-depth tests are located in
            tests/management/test_result_manager.py

    Attributes:
        client (Client): django testing client.
        requester (func): a helper function for making requests to the
            server.
        main_test (MockSuite1): the main test that sent to be run.
        token (str): the token got from the server after start_test_run.
        test_suite (MockSuite2): the first suite of the main test.
        test_case (MockCase): the first case of test_suite.
    """
    fixtures = ['resource_ut.json']

    def setUp(self):
        """Sets up a generic test control environment."""
        self.client = Client()
        self.requester = partial(request, client=self.client)
        _, token_object = request(client=self.client,
                                  path="tests/get_token", method="get")
        self.token = token_object.token

        MockSuite1.components = (MockSuite2, MockTestSuite)
        MockSuite2.components = (MockCase, MockCase1, MockCase2)
        MockTestSuite.components = (SuccessCase,)

        run_data = RunData(run_name='test_run_name')
        self.main_test = MockSuite1(run_data=run_data)
        tests_tree_dict = ClientResultManager._create_test_dict(self.main_test)
        run_data = {'run_name': self.main_test.data.run_data.run_name}

        response, _ = self.requester(path="tests/start_test_run",
                                     json_data={
                                         "run_data": run_data,
                                         "tests": tests_tree_dict,
                                         "token": self.token
                                     })
        self.assertEqual(response.status_code, http_client.NO_CONTENT)
        self.test_suite = next(iter(self.main_test))
        self.test_case = next(iter(self.test_suite))

    def test_update_run_date(self):
        """Assert that the request has the right server response."""
        response, _ = self.requester(
            path="tests/update_run_data",
            json_data={
                "token": self.token,
                "run_data": {
                    "run_name": "name2"
                }
            })
        self.assertEqual(response.status_code, http_client.NO_CONTENT)

    def test_update_resources(self):
        """Assert that the request has the right server response."""
        response, _ = self.requester(
            path="tests/update_resources",
            params={
                "token": self.token,
                "test_id": self.test_case.identifier
            },
            json_data={
                "descriptors": [{
                    "type": "rotest.management.models.ut_models."
                            "DemoResourceData",
                    "properties": {
                        "name": "available_resource1"
                    }
                }]
            })
        self.assertEqual(response.status_code, http_client.NO_CONTENT)

    def test_should_skip(self):
        """Assert that the request has the right server response."""
        response, content = self.requester(path="tests/should_skip",
                                           params={
                                               "token": self.token,
                                               "test_id":
                                                   self.test_case.identifier
                                           }, method="get")
        self.assertEqual(response.status_code, http_client.OK)
        self.assertFalse(content.should_skip)

    def test_add_test_result(self):
        """Assert that the request has the right server response."""
        response, _ = self.requester(
            path="tests/add_test_result",
            params={
                "token": self.token,
                "test_id": self.test_case.identifier
            },
            json_data={
                "result": {
                    "result_code": TestOutcome.FAILED,
                    "info": "This test failed!"
                }
            })
        self.assertEqual(response.status_code, http_client.NO_CONTENT)

    def test_start_test_stop_test(self):
        """Assert that the request has the right server response."""
        response, _ = self.requester(path="tests/start_test",
                                     params={
                                         "token": self.token,
                                         "test_id":
                                             self.test_case.identifier
                                     })

        self.assertEqual(response.status_code, http_client.NO_CONTENT)

        response, _ = self.requester(path="tests/stop_test",
                                     params={
                                         "token": self.token,
                                         "test_id":
                                             self.test_case.identifier
                                     })
        self.assertEqual(response.status_code, http_client.NO_CONTENT)

    def test_start_test_stop_composite(self):
        """Assert that the request has the right server response."""
        response, _ = self.requester(path="tests/start_composite",
                                     params={
                                         "token": self.token,
                                         "test_id":
                                             self.test_case.identifier
                                     })
        self.assertEqual(response.status_code, http_client.NO_CONTENT)

        response, _ = self.requester(path="tests/stop_composite",
                                     params={
                                         "token": self.token,
                                         "test_id":
                                             self.test_case.identifier
                                     })
        self.assertEqual(response.status_code, http_client.NO_CONTENT)
