"""
crochet.setup()

if sys.argv[1] == "runserver":
    if os.environ.get("RUN_MAIN") == "true":
        # dispatch resources to user
        backend = rotest.backend.main.WebsocketService()
        backend.create_server(INIT_LIST)
        # register post_save signal to backend
        post_save.connect(backend.send_to_client)
"""

import django
import crochet
from twisted.internet import reactor

from rotest.backend.management import BroadcastServerFactory


django.setup()
SERVER_PORT = 9000

class WebsocketService(object):
    def __init__(self):
        print("initializing websocket service")
        self.factory = BroadcastServerFactory(u'ws://0.0.0.0:{}'.format(SERVER_PORT))

    @crochet.run_in_reactor
    def create_server(self, init_list):
        self.factory.initialize_resources(init_list)
        reactor.listenTCP(SERVER_PORT, self.factory)

    def send_to_client(self, sender, instance, **kwargs):
        self.factory.cache.update_resource(sender, instance, **kwargs)
