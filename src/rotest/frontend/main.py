import json

from autobahn.twisted import WebSocketServerProtocol, WebSocketServerFactory


SERVER_PORT = 9000


def initialize_backend(factory):
    display_attrs = []
    cache = {}

    class BroadcastServerProtocol(WebSocketServerProtocol):
        """"Protocol for a Websocket server which broadcasts messages
        to clients.

        Attributes:
            WEBSOCKET_SERVER_PORT (number): the port the server listens to.
        """
        WEBSOCKET_SERVER_PORT = 9000

        def __init__(self, *args, **kwargs):
            super(BroadcastServerProtocol, self).__init__(*args, **kwargs)

        def onOpen(self):
            """"Register the client for future broadcasts."""
            self.factory.register(self)
            self.sendMessage(json.dumps(
                {
                    "event_type": "initialize-display-list",
                    "content": display_attrs
                }
            ), False)
            self.sendMessage(json.dumps(
                {
                    "event_type": "initialize-cache",
                    "content": cache
                }
            ), False)

        def connectionLost(self, reason):
            """"Unregister the client from future broadcasts."""
            super(BroadcastServerProtocol, self).connectionLost(reason)
            self.factory.unregister(self)

    class BroadcastServerFactory(WebSocketServerFactory):
        protocol = BroadcastServerProtocol

        def __init__(self, url):
            super(BroadcastServerFactory, self).__init__(url=url)
            self.clients = set()

        def broadcast(self, message, isBinary):
            for client in self.clients:
                client.sendMessage(message, isBinary=isBinary)

        def register(self, client):
            self.clients.add(client)

        def unregister(self, client):
            self.clients.remove(client)


    factory = BroadcastServerFactory(u'ws://0.0.0.0:{}'.format(SERVER_PORT))


