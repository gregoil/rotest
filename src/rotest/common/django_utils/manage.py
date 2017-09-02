#!/usr/bin/env python
import os
import sys
import django


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "all_settings")

    # Load django models. This is needed to populate the DB before using it.
    django.setup()

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
