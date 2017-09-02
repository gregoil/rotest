#!/usr/bin/env python
# pylint: disable=protected-access
import os
import sys
import platform

import django


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "all_settings")

    # Load django models. This is needed to populate the DB before using it.
    django.setup()
    if platform.system() == 'Windows':
        try:
            import win32file
            win32file._setmaxstdio(2048)

        except ImportError:
            print "Cannot find package 'win32file'. Installing it is "\
                "recommended before running the UT " \
                "(you can do so using 'pip install pypiwin32')"

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
