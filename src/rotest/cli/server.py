"""Run resource management server.

Usage:
    rotest server [options]

Options:
    -h,  --help                 Show help message and exit.
    -p <port>, --port <port>    Port for communicating with the client.
    --no-django                 Skip running the Django web server.
    --django-port <port>        Django's web server port [default: 8000].
    -D, --daemon                Run as a background process.
"""
from __future__ import print_function
import os
import sys
import subprocess

import django
import docopt

from rotest.common.config import RESOURCE_MANAGER_PORT, search_config_file
from rotest.management.server.main import ResourceManagerServer

if sys.platform != "win32":
    import daemon


def start_server(server_port, run_django_server, django_port):
    """Run the resource management server, and optionally the Django server.

    Args:
        server_port (number): port for the resource management server.
        run_django_server (bool): whether to run the Django server as well,
            or not.
        django_port (number): port for the Django server.
    """
    django_process = None
    try:
        if run_django_server:
            print("Running the Django server as well")
            app_directory = os.path.dirname(search_config_file())
            manage_py_location = os.path.join(app_directory, "manage.py")
            django_process = subprocess.Popen(
                ["python",
                 manage_py_location,
                 "runserver",
                 "0.0.0.0:{}".format(django_port)]
            )

        ResourceManagerServer(port=server_port).start()

    finally:
        if django_process is not None:
            django_process.kill()


def server():
    # Load django models before using the runner in tests.
    django.setup()

    arguments = docopt.docopt(__doc__)
    port = int(arguments["--port"] or RESOURCE_MANAGER_PORT)
    no_django = arguments["--no-django"]
    django_port = int(arguments["--django-port"])
    run_as_daemon = arguments["--daemon"]

    if run_as_daemon:
        if sys.platform == "win32":
            raise RuntimeError(
                "Cannot run as daemon on Windows")  # pragma: no cover

        print("Running in detached mode (as daemon)")
        with daemon.DaemonContext():
            start_server(server_port=port,
                         run_django_server=not no_django,
                         django_port=django_port)

    else:
        print("Running in attached mode")
        start_server(server_port=port,
                     run_django_server=not no_django,
                     django_port=django_port)
