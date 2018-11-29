from __future__ import absolute_import

from django.core.management import call_command

from rotest.api.test_control.session_cleaner import run_session_cleaner
from rotest.common.config import DJANGO_MANAGER_PORT, search_config_file


def start_server():
    """Run session manager and Django server according to the config file."""
    run_session_cleaner()
    call_command("runserver", "0.0.0.0:{}".format(DJANGO_MANAGER_PORT))
