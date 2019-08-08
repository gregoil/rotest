"""Websocket client that sends pings periodically."""
# pylint: disable=broad-except,bare-except,no-self-use
import threading

import websocket

from rotest.common import core_log


class PingingWebsocket(websocket.WebSocket):
    """Websocket client that sends pings periodically.

    Attributes:
        ping_interval (number): interval between pings in seconds, default 15.
    """
    def __init__(self, ping_interval=10, *args, **kwargs):
        super(PingingWebsocket, self).__init__(*args, **kwargs)
        self.ping_interval = ping_interval
        self.pinging_thread = None
        self.pinging_event = None

    def connect(self, *args, **kwargs):
        """Connect the websocket and start the pinging thread."""
        super(PingingWebsocket, self).connect(*args, **kwargs)
        self.pinging_event = threading.Event()
        self.pinging_thread = threading.Thread(target=self.ping_loop)
        self.pinging_thread.setDaemon(True)
        self.pinging_thread.start()

    def close(self, *args, **kwargs):
        """Close the websocket and the pinging thread."""
        super(PingingWebsocket, self).close(*args, **kwargs)
        if self.pinging_thread and self.pinging_thread.isAlive():
            self.pinging_event.set()
            self.pinging_thread.join()

    def handle_disconnection(self):
        """Called on server disconnection."""
        core_log.warning("Server disconnetion detected!")

    def ping_loop(self):
        """Ping periodically until the finish event."""
        while not self.pinging_event.wait(self.ping_interval):
            try:
                self.send("ping")

            except:  # noqa
                self.handle_disconnection()
                break
