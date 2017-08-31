"""Resource manager server runner.

Note:
    By default, resource manager server supports only the basic resources
    defined under Rotest. In order to extend the resources, set the
    "DJANGO_SETTINGS_MODULE" environment variable to point to the extended
    package's settings module.
"""
# pylint: disable=redefined-outer-name
import sys
import logging
import argparse

import django
from twisted.internet.protocol import ServerFactory
from twisted.internet.selectreactor import SelectReactor

from worker import Worker
from manager import ManagerThread
from rotest.management.common.parsers import DEFAULT_PARSER
from rotest.management.common.utils import DEFAULT_SERVER_PORT
from rotest.common.log import (ROTEST_WORK_DIR, LOG_FORMAT, ColoredFormatter,
                               get_test_logger)


LOG_NAME = 'resource_manager'


def get_logger(log_to_screen):
    """Return the logger for resource manager.

    Args:
        log_to_screen (bool): Enable log prints to screen.

    Returns:
        the logger of the resource manager.
    """
    logger = get_test_logger(LOG_NAME, ROTEST_WORK_DIR)

    if log_to_screen is True:
        log_handler = logging.StreamHandler(stream=sys.stdout)
        log_handler.setFormatter(ColoredFormatter(LOG_FORMAT))
        logger.addHandler(log_handler)

    return logger


class ResourceManagerServer(object):
    """Resource manager server."""

    def __init__(self, port=DEFAULT_SERVER_PORT,
                 parser=DEFAULT_PARSER, log_to_screen=True):
        """Initialize the resource manager server.

        Args:
            port (number): client listener port.
            parser (object): messages parser of type `AbstractParser`.
            log_to_screen (bool): Enable log prints to screen.
        """
        self.logger = get_logger(log_to_screen)

        self._factory = ServerFactory()
        self._factory.protocol = Worker
        self._factory.logger = self.logger
        self._factory.protocol.parser = parser()

        self._port = port
        self._reactor = SelectReactor()
        self._reactor.listenTCP(port, self._factory)

        self._resource_manager = ManagerThread(self._reactor, self.logger)
        self._factory.request_queue = self._resource_manager.request_queue

    def start(self):
        """Start resource manager server.

         * Starts resource manager thread.
         * Starts client listener.
        """
        self.logger.debug("Starting resource manager, port:%d", self._port)
        self._resource_manager.start()
        self._reactor.run()

    def stop(self):
        """Stop the resource manager server."""
        self.logger.debug("Stopping resource manager server")
        self._resource_manager.stop()
        self._reactor.callFromThread(self._reactor.stop)


def main():
    """Resource manager main method.

    Loads the Django models if needed and starts a manager server.
    """
    django.setup()

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", dest="port", help="Server's listener port",
                        type=int, action='store', default=DEFAULT_SERVER_PORT)

    args = parser.parse_args()

    ResourceManagerServer(port=args.port).start()


if __name__ == '__main__':
    main()
