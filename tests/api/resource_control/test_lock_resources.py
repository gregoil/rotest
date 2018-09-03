"""Basic unittests for the server resource control operations."""
import httplib
from functools import partial

from django.contrib.auth.models import User
from django.test import Client, TransactionTestCase

from tests.api.utils import request
from rotest.management.models import DemoComplexResourceData


class TestLockResources(TransactionTestCase):
    """Assert operations of lock resources request."""
    fixtures = ['resource_ut.json']

    def setUp(self):
        """Setup test environment."""
        self.client = Client()
        self.requester = partial(request, self.client,
                                 "resources/lock_resources")

    def test_lock_empty(self):
        """Assert trying to lock no resources."""
        response, content = self.requester(
            json_data={
                "descriptors": [],
                "timeout": 0
            })
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(content.resource_descriptors), 0)

    def test_lock_valid_resource(self):
        """Assert trying to lock valid resource."""
        response, content = self.requester(
            json_data={
                "descriptors": [
                    {
                        "type": "rotest.management.models.ut_models."
                                "DemoResourceData",
                        "properties": {}
                    }
                ],
                "timeout": 0
            })
        self.assertEqual(response.status_code, httplib.OK)
        self.assertEqual(len(content.resource_descriptors), 1)

    def test_invalid_resource_field(self):
        """Assert invalid resource field filter requested."""
        response, _ = self.requester(
            json_data={
                "descriptors": [
                    {
                        "type": "rotest.management.models.ut_models."
                                "DemoResourceData",
                        "properties": {
                            "invalid_field": "field1"
                        }
                    }
                ],
                "timeout": 0
            })
        self.assertEqual(response.status_code, httplib.BAD_REQUEST)

    def test_lock_complex(self):
        """Assert trying to lock complex resource."""
        resources = DemoComplexResourceData.objects.filter(
            name='complex_resource1')

        resource, = resources
        sub_resource = resource.demo1

        self.assertTrue(resource.is_available())
        self.assertTrue(sub_resource.is_available())
        response, _ = self.requester(
            json_data={
                "descriptors": [
                    {
                        "type": "rotest.management.models.ut_models."
                                "DemoComplexResourceData",
                        "properties": {}
                    }
                ],
                "timeout": 0
            })
        # refresh from db
        resources = DemoComplexResourceData.objects.filter(
            name='complex_resource1')
        resource, = resources
        sub_resource = resource.demo1

        self.assertEqual(response.status_code, httplib.OK)
        self.assertFalse(resource.is_available())
        self.assertFalse(sub_resource.is_available())

    def test_lock_complex_sub_resource_unavailable(self):
        """Assert trying to lock resource with sub-resource unavailable."""
        resources = DemoComplexResourceData.objects.filter(
            name='complex_resource1')

        resource, = resources
        sub_resource = resource.demo1

        sub_resource.reserved = "unknown_person"
        sub_resource.save()

        response, _ = self.requester(
            json_data={
                "descriptors": [
                    {
                        "type": "rotest.management.models.ut_models."
                                "DemoComplexResourceData",
                        "properties": {}
                    }
                ],
                "timeout": 0
            })

        resources = DemoComplexResourceData.objects.filter(
            name='complex_resource1')
        resource, = resources
        sub_resource = resource.demo1

        self.assertEqual(response.status_code, httplib.BAD_REQUEST)
        # no reserved nor owner for main resource
        self.assertFalse(resource.reserved)
        self.assertFalse(resource.owner)
        self.assertFalse(resource.is_available())

        # sub resource left untouched
        self.assertFalse(sub_resource.is_available())
        self.assertEqual(sub_resource.reserved, "unknown_person")


class TestLockResourcesInvalid(TransactionTestCase):
    """Assert operations of invalid lock resources requests."""

    def setUp(self):
        """Setup test environment."""
        self.client = Client()
        self.requester = partial(request, self.client,
                                 "resources/lock_resources")

    def test_invalid_input(self):
        """Assert invalid request."""
        # empty data
        response, _ = self.requester(json_data={})
        self.assertEqual(response.status_code, httplib.INTERNAL_SERVER_ERROR)

    def test_no_user_in_db(self):
        """Assert locking user not in db."""
        # localhost is not in db
        response, content = self.requester(
            json_data={
                "descriptors": [],
                "timeout": 0
            })
        self.assertEqual(response.status_code, httplib.BAD_REQUEST)
        self.assertEqual(content.details,
                         "User localhost has no matching object in the DB")

    def test_invalid_content_type(self):
        """Assert invalid request content type."""
        # invalid content type
        response, _ = self.requester(content_type="text/html")
        self.assertEqual(response.status_code, httplib.INTERNAL_SERVER_ERROR)

    def test_invalid_resource(self):
        """Assert invalid resource requested."""
        User.objects.create_user(username='localhost',
                                 email='email@email.com',
                                 password='localhost')
        response, content = self.requester(
            json_data={
                "descriptors": [
                    {
                        "type": "invalidmodule.invalidtype",
                        "properties": {}
                    }
                ],
                "timeout": 0
            })
        self.assertEqual(response.status_code, httplib.BAD_REQUEST)
        self.assertEqual(content.details,
                         "Failed to extract type u'invalidmodule.invalidtype'."
                         " Reason: No module named invalidmodule.")

        # no available resources
        response, content = self.requester(
            json_data={
                "descriptors": [
                    {
                        "type": "rotest.management.models.ut_models."
                                "DemoResourceData",
                        "properties": {}
                    }
                ],
                "timeout": 0
            })

        self.assertEqual(response.status_code, httplib.BAD_REQUEST)
        self.assertTrue(content.details.startswith(
            "No existing resource meets the requirements"))
