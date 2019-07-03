"""Consumers for channels."""
from __future__ import absolute_import

import json

from channels.log import setup_logger

from rotest.core.models import GeneralData, CaseData
from rotest.core.models.case_data import TestOutcome
from rotest.api.test_control.middleware import SESSIONS
from rotest.api.resource_control import ReleaseResources


CHANNEL_TO_TOKEN = {}


def close_session(session_key):
    """Close a REST session by its key.

    This releases the session's resources and closes any unfinished tests.

    Args:
        session_key (str): token of the session.
    """
    session_data = SESSIONS[session_key]
    for test in session_data.all_tests.values():
        if test.status == GeneralData.IN_PROGRESS:
            if isinstance(test, CaseData):
                test.update_result(TestOutcome.ERROR, "Session closed")

            else:
                test.end()

            test.save()

    for resource in session_data.resources:
        ReleaseResources.release_resource(resource, username=None)

    SESSIONS.pop(session_key)


def ws_connect(message):
    """Connect a new websocket client."""
    message.reply_channel.send({"accept": True})


def ws_receive(message):
    """Receive a message from a websocket.

    As of now, that message should be either 'ping' or the REST session token.
    """
    content = message.content['text']
    if content != "ping":
        content = json.loads(content)
        token = content['token']
        setup_logger("server").info("Registering client with token %r", token)
        CHANNEL_TO_TOKEN[message.reply_channel.name] = token


def ws_disconnect(message):
    """Disconnect a websocket client, cleaning its session."""
    if message.reply_channel.name in CHANNEL_TO_TOKEN:
        token = CHANNEL_TO_TOKEN[message.reply_channel.name]
        setup_logger("server").info("Cleaning session for client %r", token)
        close_session(token)
