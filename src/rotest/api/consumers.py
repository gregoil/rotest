"""Consumers for channels."""
from __future__ import absolute_import

import json

from rotest.core.models import GeneralData, CaseData
from rotest.core.models.case_data import TestOutcome
from rotest.api.test_control.middleware import SESSIONS
from rotest.api.resource_control import ReleaseResources


CHANNEL_TO_TOKEN = {}


def close_session(session_key):
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
    message.reply_channel.send({"accept": True})


def ws_receive(message):
    content = message.content['text']
    if content != "ping":
        content = json.loads(content)
        token = content['token']
        CHANNEL_TO_TOKEN[message.reply_channel.name] = token


def ws_disconnect(message):
    if message.reply_channel.name in CHANNEL_TO_TOKEN:
        print("Cleaning session data")
        close_session(CHANNEL_TO_TOKEN[message.reply_channel.name])

