"""Basic unittests for the server resource control operations."""
import httplib
from functools import partial

from django.db.models.query_utils import Q
from django.test import Client, TransactionTestCase

from tests.api.utils import request
from rotest.management.models import DemoResourceData


class TestUpdateFields(TransactionTestCase):
    """Assert operations of update resources request."""
    fixtures = ['resource_ut.json']

    def setUp(self):
        """Setup test environment."""
        self.client = Client()
        self.requester = partial(request, client=self.client,
                                 path="resources/update_fields",
                                 method="put")

    def test_update_all_resources_fields(self):
        """Assert that updating all resources when no filter exists - works."""
        response, _ = self.requester(json_data={
            "resource_descriptor": {
                "type": "rotest.management.models.ut_models."
                        "DemoResourceData",
                "properties": {}
            },
            "changes": {
                "reserved": "A_User"
            }
        })
        self.assertEqual(response.status_code, httplib.NO_CONTENT)
        resources = DemoResourceData.objects.all()
        for resource in resources:
            self.assertEqual(resource.reserved, "A_User")

    def test_update_specific_resource_fields(self):
        """Assert that updating specific resource - works."""
        response, _ = self.requester(json_data={
            "resource_descriptor": {
                "type": "rotest.management.models.ut_models."
                        "DemoResourceData",
                "properties": {
                    "name": "available_resource1"
                }
            },
            "changes": {
                "reserved": "A_User"
            }
        })
        self.assertEqual(response.status_code, httplib.NO_CONTENT)
        resources = DemoResourceData.objects.filter(name="available_resource1")
        for resource in resources:
            self.assertEqual(resource.reserved, "A_User")

        resources = DemoResourceData.objects.filter(
            ~Q(name="available_resource1"))

        for resource in resources:
            self.assertNotEqual(resource.reserved, "A_User")
