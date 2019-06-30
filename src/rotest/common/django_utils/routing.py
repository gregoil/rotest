"""Routing directing."""
from __future__ import absolute_import

from channels.routing import route
from rotest.api.consumers import ws_connect, ws_disconnect


channel_routing = [
    route('websocket.connect', ws_connect),
    route('websocket.disconnect', ws_disconnect),
]
