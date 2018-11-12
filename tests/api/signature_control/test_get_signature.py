"""Basic unittests for the server resource control operations."""
from __future__ import absolute_import

from functools import partial

from six.moves import http_client
from django.test import Client, TransactionTestCase

from tests.api.utils import request
from rotest.core.models import SignatureData


class TestGetOrCreateSignature(TransactionTestCase):
    """Assert operations of get or create signature request."""
    fixtures = ['resource_ut.json']

    def setUp(self):
        """Setup test environment."""
        self.client = Client()
        self.requester = partial(request, method="get", client=self.client,
                                 path="signatures/get_or_create")

    def test_new_signature(self):
        """Validate creating and then using a new signature."""
        response, content = self.requester(json_data={
            "error": "new error traceback"
        })

        self.assertEqual(response.status_code, http_client.OK)
        self.assertTrue(content.is_new)
        self.assertEqual(content.link, "")

        response, content = self.requester(json_data={
            "error": "new error traceback"
        })

        self.assertEqual(response.status_code, http_client.OK)
        self.assertFalse(content.is_new)

    def test_precise_match(self):
        """Validate match with a simple string match."""
        link = "Some link"
        SignatureData.objects.create(pk=1, link=link,
                                     pattern="some traceback")

        response, content = self.requester(json_data={
            "error": "some traceback"
        })

        self.assertEqual(response.status_code, http_client.OK)
        self.assertFalse(content.is_new)
        self.assertEqual(content.id, 1)
        self.assertEqual(content.link, link)

    def test_pattern_match(self):
        """Validate match with a regular expression pattern."""
        link = "Some link"
        error = "error.level over 9000.0"
        pattern = SignatureData.create_pattern(error)
        self.assertNotEqual(error, pattern)

        SignatureData.objects.create(pk=2, link=link, pattern=pattern)

        response, content = self.requester(json_data={
            "error": error
        })

        self.assertEqual(response.status_code, http_client.OK)
        self.assertFalse(content.is_new)
        self.assertEqual(content.id, 2)
        self.assertEqual(content.link, link)
