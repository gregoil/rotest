"""Basic unittests for the server resource control operations."""
from __future__ import absolute_import

from functools import partial

from six.moves import http_client
from django.test import Client, TransactionTestCase

from rotest.management.models import DemoResourceData

from tests.api.utils import request


class TestQueryResourcesInvalid(TransactionTestCase):
    """Assert operations of invalid query resources request."""
    def setUp(self):
        """Setup test environment."""
        self.client = Client()
        self.requester = partial(request, client=self.client,
                                 path="resources/query_resources")

    def test_query_invalid_resource(self):
        response, _ = self.requester(json_data={
            "type": "invalidmodule.invalidtype",
            "properties": {}
        })
        self.assertEqual(response.status_code, http_client.BAD_REQUEST)

    def test_query_unavailable_resource(self):
        response, content = self.requester(json_data={
            "type": "rotest.management.models.ut_models."
                    "DemoResourceData",
            "properties": {}
        })
        self.assertEqual(response.status_code, http_client.BAD_REQUEST)
        self.assertTrue(content.details.startswith(
            "No existing resource meets the requirements"))


class TestQueryResources(TransactionTestCase):
    """Assert operations of query resources request."""
    fixtures = ['resource_ut.json']

    def setUp(self):
        """Setup test environment."""
        self.client = Client()
        self.requester = partial(request, client=self.client,
                                 path="resources/query_resources")

    def test_query_valid_resource(self):
        count = len(DemoResourceData.objects.all())
        response, content = self.requester(json_data={
            "type": "rotest.management.models.ut_models."
                    "DemoResourceData",
            "properties": {}
        })
        self.assertEqual(response.status_code, http_client.OK)
        self.assertEqual(len(content.resource_descriptors), count)

    def test_query_valid_resource_with_filter(self):
        count = len(DemoResourceData.objects.filter(owner=""))
        response, content = self.requester(json_data={
            "type": "rotest.management.models.ut_models."
                    "DemoResourceData",
            "properties": {
                "owner": ""
            }
        })
        self.assertEqual(response.status_code, http_client.OK)
        self.assertEqual(len(content.resource_descriptors), count)
