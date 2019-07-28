from __future__ import absolute_import

import sys

import pkg_resources
import django
from django.core.management import call_command

from rotest.common import core_log
from rotest.common.config import DJANGO_MANAGER_PORT


def start_server():
    """Run session manager and Django server according to the config file."""
    django.setup()

    for entry_point in \
            pkg_resources.iter_entry_points("rotest.cli_server_actions"):
        core_log.debug("Applying server entry point %s", entry_point.name)
        extension_action = entry_point.load()
        extension_action()

    server_args = "0.0.0.0:{}".format(DJANGO_MANAGER_PORT)
    if sys.platform == "win32":
        sys.argv = ["-m", "django", "runserver", server_args]

    call_command("runserver", server_args)
