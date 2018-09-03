#!/usr/bin/env python
import os
import sys

from rotest.cli.client import main as run
from rotest.management.utils.shell import main as shell
from rotest.common.config import DJANGO_MANAGER_PORT, search_config_file


def start_server():
    """Start Django server with the port from the config file.

    Attempt to use the project's manage.py file if exists, otherwise use
    the general 'django-admin' command.
    """
    app_directory = os.path.dirname(search_config_file())
    manage_py_location = os.path.join(app_directory, "manage.py")
    if os.path.exists(manage_py_location):
        command = "python " + manage_py_location

    else:
        command = "django-admin"

    command += " runserver 0.0.0.0:{}".format(DJANGO_MANAGER_PORT)

    os.system(command)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "shell":
        shell()

    elif len(sys.argv) > 1 and sys.argv[1] == "server":
        start_server()

    else:
        run()
