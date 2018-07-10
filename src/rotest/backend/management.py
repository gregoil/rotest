import json

from django.contrib import admin
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory

from cache import Cache


class BroadcastServerProtocol(WebSocketServerProtocol):
    """"Protocol for a Websocket server which broadcasts messages to clients."""

    def __init__(self, *args, **kwargs):
        super(BroadcastServerProtocol, self).__init__(*args, **kwargs)

    def onOpen(self):
        """"Register the client for future broadcasts."""
        super(BroadcastServerProtocol, self).onOpen()
        self.factory.register(self)

    def connectionLost(self, reason):
        """"Unregister the client from future broadcasts."""
        super(BroadcastServerProtocol, self).connectionLost(reason)
        self.factory.unregister(self)


class BroadcastServerFactory(WebSocketServerFactory):
    protocol = BroadcastServerProtocol

    def __init__(self, url):
        super(BroadcastServerFactory, self).__init__(url=url)
        self.clients = set()
        self.cache = Cache(self)

    def initialize_resources(self, resources):
        self.cache.initialize_resources_cache(resources)
        display_attrs = {
            resource.__name__: admin.site._registry[resource].list_display
            for resource in resources
        }
        self.cache.initialize_display_list_cache(display_attrs)

        # send to all users the extracted resources
        self.cache.update_users_display_list()
        self.cache.update_users_resources_cache()

    def broadcast(self, message, isBinary):
        for client in self.clients:
            client.sendMessage(message, isBinary=isBinary)

    def register(self, client):
        self.clients.add(client)
        client.sendMessage(json.dumps(
                {
                    "event_type": "initialize-display-list",
                    "content": self.cache.display_list_cache
                }
            ), False)
        client.sendMessage(json.dumps(
                {
                    "event_type": "initialize-cache",
                    "content": self.cache.resources_cache
                }
            ), False)

    def unregister(self, client):
        self.clients.remove(client)
