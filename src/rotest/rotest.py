#!/usr/bin/env python
import sys


def do_discover(start_dir):
    from unittest import loader
    from rotest.core import TestCase, TestFlow
    discovered_tests = loader.discover(start_dir, None, None)._tests
    all_tests = []
    for test_class in discovered_tests:
        if isinstance(test_class, (TestCase, TestFlow)) and \
                getattr(test_class, "__test__", True) is True:

            all_tests.append(test_class)

    for test_class in all_tests:
        print test_class


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
        from django.core import management
        management.execute_from_command_line()


if __name__ == "__main__":
    main()
