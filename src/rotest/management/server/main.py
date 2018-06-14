"""Run resource manager server."""
import sys
import logging

from twisted.internet.protocol import ServerFactory
from twisted.internet.selectreactor import SelectReactor

from rotest.management.server.worker import Worker
from rotest.common.config import RESOURCE_MANAGER_PORT
from rotest.management.server.manager import ManagerThread
from rotest.management.common.parsers import DEFAULT_PARSER
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

    if log_to_screen:
        log_handler = logging.StreamHandler(stream=sys.stdout)
        log_handler.setFormatter(ColoredFormatter(LOG_FORMAT))
        logger.addHandler(log_handler)

    return logger


class ResourceManagerServer(object):
    """Resource manager server."""

    def __init__(self, port=RESOURCE_MANAGER_PORT,
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
