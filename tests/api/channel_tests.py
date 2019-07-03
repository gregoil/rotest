"""Tests for consumer behavior."""
import json

import mock
from channels.test import ChannelTestCase, Client


class ChannelTests(ChannelTestCase):
    """Tests for consumer behavior."""

    TEST_TOKEN = 100

    @mock.patch('rotest.api.consumers.close_session')
    def test_close_session(self, mock_callback):
        """Check that 'close_session' is called at disconnect."""
        client = Client()
        client.send_and_consume('websocket.connect', {})
        message_content = {'text': json.dumps({"token": self.TEST_TOKEN})}
        client.send_and_consume('websocket.receive', message_content)
        client.send_and_consume('websocket.disconnect', {})
        mock_callback.assert_called_with(self.TEST_TOKEN)
