"""Routing directing."""
from __future__ import absolute_import

from channels.routing import route
from rotest.api.consumers import ws_connect, ws_disconnect, ws_receive


channel_routing = [
    route('websocket.connect', ws_connect),
    route('websocket.receive', ws_receive),
    route('websocket.disconnect', ws_disconnect),
]
