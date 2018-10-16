"""Basic unittests for the server resource control operations."""
from __future__ import absolute_import

from functools import partial

from six.moves import http_client
from django.test import Client, TransactionTestCase

from tests.api.utils import request
from rotest.api.test_control.middleware import SESSIONS
from rotest.management.models import DemoComplexResourceData


class TestCleanupUser(TransactionTestCase):
    """Assert operations of cleanup user request."""
    fixtures = ['resource_ut.json']

    def setUp(self):
        """Setup test environment."""
        self.client = Client()
        _, token_object = request(client=self.client,
                                  path="tests/get_token", method="get")
        self.token = token_object.token
        self.requester = partial(request, client=self.client,
                                 path="resources/cleanup_user")

    def test_no_resources_locked(self):
        """Assert response - cleanup when user didn't lock anything."""
        response, _ = self.requester(json_data={"token": self.token})
        self.assertEqual(response.status_code, http_client.NO_CONTENT)

    def test_release_owner_complex_resource(self):
        """Assert response - cleanup of complex resource."""
        resources = DemoComplexResourceData.objects.filter(
            name='complex_resource1')

        resource, = resources
        sub_resource = resource.demo1

        resource.owner = "localhost"
        sub_resource.owner = "localhost"
        resource.save()
        sub_resource.save()
        SESSIONS[self.token].resources = [resource]
        response, _ = self.requester(json_data={"token": self.token})
        self.assertEqual(response.status_code, http_client.NO_CONTENT)

        resources = DemoComplexResourceData.objects.filter(
            name='complex_resource1')

        resource, = resources
        sub_resource = resource.demo1

        self.assertEqual(resource.owner, "")
        self.assertEqual(sub_resource.owner, "")
