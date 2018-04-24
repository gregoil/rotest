"""Run resource manager server.

Usage:
    rotest-server [--server-port <port>] [--run-django-server]
                  [--django-port <port>] [-D | --daemon]

Options:
    -h --help
        show this help message and exit

    --server-port <port>
        port for communicating with the client

    --run-django-server
        run the Django frontend as well

    --django-port <port>
        set Django's port [default: 8000]

    -D --daemon
        run as a daemon
"""
# pylint: disable=redefined-outer-name
import sys
import logging
import subprocess

import docopt
import django
from twisted.internet.protocol import ServerFactory
from twisted.internet.selectreactor import SelectReactor

from rotest.management.server.worker import Worker
from rotest.common.config import RESOURCE_MANAGER_PORT
from rotest.management.server.manager import ManagerThread
from rotest.management.common.parsers import DEFAULT_PARSER
from rotest.common.log import (ROTEST_WORK_DIR, LOG_FORMAT, ColoredFormatter,
                               get_test_logger)

if sys.platform != "win32":
    import daemon


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


def start_server(server_port, run_django_server, django_port):
    """Run the resource management server, and optionally the Django frontend.

    Args:
        server_port (number): port for the resource management server.
        run_django_server (bool): whether to run the Django frontend as well,
            or not.
        django_port (number): port for the Django frontend.
    """
    django_process = None
    try:
        if run_django_server:
            print "Running the Django server as well"
            django_process = subprocess.Popen(
                ["django-admin",
                 "runserver",
                 "0.0.0.0:{}".format(django_port)])

        ResourceManagerServer(port=server_port).start()

    finally:
        if django_process is not None:
            django_process.kill()


def main():
    """Resource manager main method.

    Loads the Django models if needed and starts a manager server.
    """
    django.setup()

    args = docopt.docopt(__doc__)
    server_port = args["--server-port"]

    if server_port is None:
        server_port = RESOURCE_MANAGER_PORT
    else:
        server_port = int(server_port)

    run_django_server = args["--run-django-server"]
    django_port = int(args["--django-port"])
    run_as_daemon = args["--daemon"]

    if run_as_daemon:
        if sys.platform == "win32":
            raise ValueError("Cannot run as daemon on Windows")

        print "Running in detached mode (as daemon)"
        with daemon.DaemonContext(stdout=None):
            start_server(server_port=server_port,
                         run_django_server=run_django_server,
                         django_port=django_port)

    else:
        print "Running in attached mode"
        start_server(server_port=server_port,
                     run_django_server=run_django_server,
                     django_port=django_port)


if __name__ == '__main__':
    main()
