#!/usr/bin/env python
# pylint: disable=protected-access
import os
import sys
import platform

import django
from rotest.common import core_log


def main():
    core_log.info("Using UT settings")
    # Load django models. This is needed to populate the DB before using it
    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "rotest.common.django_utils.ut_settings")

    django.setup()
    if platform.system() == 'Windows':
        try:
            core_log.debug("Setting 2048 as the file descriptors limit")
            import win32file
            win32file._setmaxstdio(2048)

        except ImportError:
            raise RuntimeError("Cannot find package 'win32file'. Installing "
                               "it is recommended before running the UT (you "
                               "can do so using 'pip install pypiwin32')")

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
