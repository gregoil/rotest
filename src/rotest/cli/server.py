import sys
import subprocess

import click
import django

from rotest.common.config import RESOURCE_MANAGER_PORT
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
            click.secho("Running the Django server as well")
            django_process = subprocess.Popen(
                ["django-admin",
                 "runserver",
                 "0.0.0.0:{}".format(django_port)]
            )

        ResourceManagerServer(port=server_port).start()

    finally:
        if django_process is not None:
            django_process.kill()


@click.command(help="Run resource management server.",
               context_settings=dict(
                   help_option_names=['-h', '--help'],
               ))
@click.option("--port",
              type=int,
              default=RESOURCE_MANAGER_PORT,
              show_default=True,
              help="Port for communicating with the client.")
@click.option("--no-django",
              is_flag=True,
              default=False,  # meaning, Django server is by default being ran
              help="Skip running the Django web server.")
@click.option("--django-port",
              type=int,
              default=8000,
              show_default=True,
              help="Django's web server port.")
@click.option("run_as_daemon",
              "--daemon", "-D",
              is_flag=True,
              show_default=True,
              help="Run as a daemon.")
def server(port, no_django, django_port, run_as_daemon):
    """Run the rotest resource manager server.

    Args:
        port (number): port to be exposed for the clients' usage.
        no_django (book): not running the Django server as well.
        django_port (number): port to be exposed by the Django server.
        run_as_daemon (bool): whether to run the server in the background
            or not.
    """
    django.setup()

    if run_as_daemon:
        if sys.platform == "win32":
            raise ValueError(
                "Cannot run as daemon on Windows")  # pragma: no cover

        click.secho("Running in detached mode (as daemon)", bold=True)
        with daemon.DaemonContext(stdout=None):
            start_server(server_port=port,
                         run_django_server=not no_django,
                         django_port=django_port)

    else:
        click.secho("Running in attached mode", bold=True)
        start_server(server_port=port,
                     run_django_server=not no_django,
                     django_port=django_port)
