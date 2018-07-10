"""
factory = rotest.backend.main.create_server(INIT_LIST)

Add the following code to your application to allow resource updating:

def send_to_client(sender, instance, **kwargs):
    factory.cache.update_resource(sender, instance, **kwargs)

print("handler connected")
post_save.connect(send_to_client)
"""

import os
import signal
import threading

from twisted.internet import reactor

from rotest.backend.management import BroadcastServerFactory


SERVER_PORT = 9000

def create_server(init_list):
    print("initializing websocket service")
    factory = BroadcastServerFactory(u'ws://0.0.0.0:{}'.format(SERVER_PORT))

    factory.initialize_resources(init_list)
    reactor.listenTCP(SERVER_PORT, factory)

    threading.Thread(target=reactor.run, args=(False,)).start()


    def kill_thread(signal, frame):
        reactor.stop()
        os._exit(1)

    signal.signal(signal.SIGINT, kill_thread)

    return factory
