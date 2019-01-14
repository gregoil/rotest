from __future__ import absolute_import

import pkg_resources
import django
from django.core.management import call_command

from rotest.common import core_log
from rotest.common.config import DJANGO_MANAGER_PORT
from rotest.api.test_control.session_cleaner import run_session_cleaner


def start_server():
    """Run session manager and Django server according to the config file."""
    django.setup()

    for entry_point in \
            pkg_resources.iter_entry_points("rotest.cli_server_actions"):
        core_log.debug("Applying server entry point %s", entry_point.name)
        extension_action = entry_point.load()
        extension_action()

    run_session_cleaner()
    call_command("runserver", "0.0.0.0:{}".format(DJANGO_MANAGER_PORT))
