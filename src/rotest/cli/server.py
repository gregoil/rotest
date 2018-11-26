from __future__ import absolute_import
import os

from rotest.api.test_control.session_cleaner import run_session_cleaner
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
    run_session_cleaner()
