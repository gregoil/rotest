"""Consumers for channels."""
from __future__ import absolute_import

from channels import Group


def ws_connect(message):
    Group('users').add(message.reply_channel)
    print("User connected %s: %s" % (message, message.__dict__))
    message.reply_channel.send({"accept": True})


def ws_disconnect(message):
    Group('users').discard(message.reply_channel)
    print("User diconnected %s" % (message,))
