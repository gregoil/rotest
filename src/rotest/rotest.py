#!/usr/bin/env python
import sys

from django.core import management


def do_discover(start_dir):
    pass


def main():
    # Rotest admin script:
    argv = sys.argv[1:]
    if argv[0] == "server":
        from rotest.management.server.main import main
        main()

    elif argv[0] == "discover":
        pass

    # Default option - pass control to django-admin:
    else:
        management.execute_from_command_line()


if __name__ == "__main__":
    main()
