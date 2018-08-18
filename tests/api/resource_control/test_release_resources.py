"""Basic unittests for the server resource control operations."""
import httplib
from functools import partial

from django.test import Client, TransactionTestCase

from tests.api.utils import request
from rotest.management.models import DemoComplexResourceData, DemoResourceData


class TestReleaseResources(TransactionTestCase):
    """Assert operations of release resources request."""
    fixtures = ['resource_ut.json']

    def setUp(self):
        """Setup test environment."""
        self.client = Client()
        self.requester = partial(request, client=self.client,
                                 path="resources/release_resources")

    def test_resource_doesnt_exist(self):
        """Assert trying to release invalid resource fails."""
        response, _ = self.requester(json_data={
            "resources": ["invalid_resource_name"]
        })

        self.assertEqual(response.status_code, httplib.BAD_REQUEST)

    def test_release_complex_resource_with_sub_resource_available(self):
        """Assert trying to release complex resource - sub-resource available.

        Response should be 400 (Bad Request).
        Resource should be released.
        SubResource should be the same - released.
        """
        resources = DemoComplexResourceData.objects.filter(
            name='complex_resource1')

        resource, = resources
        resource.owner = "localhost"
        resource.save()

        response, content = self.requester(json_data={
            "resources": ["complex_resource1"]
        })

        # bad request because sub-resources was not owned.
        self.assertEqual(response.status_code, httplib.BAD_REQUEST)
        self.assertEqual(len(content.errors["complex_resource1"]), 2)
        # refresh from db
        resources = DemoComplexResourceData.objects.filter(
            name='complex_resource1')

        resource, = resources
        sub_resource = resource.demo1
        sub_resource2 = resource.demo2

        self.assertEqual(resource.owner, "")
        self.assertEqual(sub_resource.owner, "")
        self.assertEqual(sub_resource2.owner, "")

    def test_try_to_release_not_owned_resource(self):
        """Assert that trying to release unowned resource fails."""
        resources = DemoResourceData.objects.filter(
            name='available_resource1')

        resource, = resources
        resource.owner = "unknown_user"
        resource.save()

        response, _ = self.requester(json_data={
            "resources": ["available_resource1"]
        })
        # refresh from db
        resources = DemoResourceData.objects.filter(
            name='available_resource1')

        resource, = resources
        self.assertEqual(response.status_code, httplib.BAD_REQUEST)
        self.assertEqual(resource.owner, "unknown_user")

    def test_valid_release(self):
        """Assert valid resource release."""
        resources = DemoResourceData.objects.filter(
            name='available_resource1')

        resource, = resources
        resource.owner = "localhost"
        resource.save()

        response, _ = self.requester(json_data={
            "resources": ["available_resource1"]
        })
        # refresh from db
        resources = DemoResourceData.objects.filter(
            name='available_resource1')

        resource, = resources
        self.assertEqual(response.status_code, httplib.NO_CONTENT)
        self.assertEqual(resource.owner, "")
