"""Unittests for the swagger page."""
import httplib
from functools import partial

from django.test import TestCase, Client

from tests.api.utils import request


class TestSwagger(TestCase):
    """Tests for the swagger page."""
    fixtures = ['resource_ut.json']

    def setUp(self):
        """Setup test environment."""
        self.client = Client()
        self.requester = partial(request, client=self.client)

    def test_swagger_json(self):
        """Assert swagger.json page loads"""
        response, _ = self.requester(path="swagger.json", method="get")
        self.assertEqual(response.status_code, httplib.OK)

    def test_swagger_page(self):
        """Assert swagger ui page loads."""
        response, _ = self.requester(path="", method="get")
        self.assertEqual(response.status_code, httplib.OK)
