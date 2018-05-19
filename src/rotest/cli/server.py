import sys

import django

import click

from rotest.common.config import RESOURCE_MANAGER_PORT
from rotest.management.server.main import ResourceManagerServer

if sys.platform != "win32":
    import daemon


@click.command(help="Run resource management server.",
               context_settings=dict(
                   help_option_names=['-h', '--help'],
               ))
@click.option("--port",
              type=int,
              default=RESOURCE_MANAGER_PORT,
              show_default=True,
              help="Port for communicating with the client")
@click.option("run_as_daemon",
              "--daemon", "-D",
              is_flag=True,
              show_default=True,
              help="Run as a daemon")
def server(port, run_as_daemon):
    """Run the rotest resource manager server.

    Args:
        port: port to be exposed for clients use.
        run_as_daemon: whether to run the server in the background or not.
    """
    django.setup()

    if run_as_daemon:
        if sys.platform == "win32":
            raise ValueError("Cannot run as daemon on Windows")

        click.secho("Running in detached mode (as daemon)", bold=True)
        with daemon.DaemonContext(stdout=None):
            ResourceManagerServer(port=port).start()

    else:
        click.secho("Running in attached mode", bold=True)
        ResourceManagerServer(port=port).start()
