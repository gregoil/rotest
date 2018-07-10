import json

import os
from django.contrib import admin
from django.db.models.signals import post_save
from twisted.internet import reactor

from backend import actions

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

    def initialize_resources(resources):
        actions.initialize_resources(resources)
        display_attrs = {
            resource.__name__: admin.site._registry[resource].list_display
            for resource in resources
        }
        actions.update_users_display_list(factory, display_attrs)
        actions.update_users_cache(factory, cache)

    def run():
        initialize_resources(INIT_RESOURCES)

        reactor.listenTCP(SERVER_PORT, factory)

        threading.Thread(target=reacto.run, args=(False,)).start()


    def send_to_server(sender, instance, **kwargs):
        actions.update_resource(cache, factory, sender, instance, **kwargs)

    post_save.connect(send_to_server)


    def kill_thread():
        reactor.stop()
        os._exit(0)

