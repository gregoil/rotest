#!/usr/bin/env python
import os
import sys
from unittest import loader
from itertools import chain

from rotest.core import TestSuite, TestCase, TestFlow, runner
from rotest.management.server.main import main as server_main


def do_discover(path):
    """Find and return all Rotest test items discovered under a directory.

    Filters the tests so only return subclasses of TestCase and TestFlow
    that their __test__ static field doesn't exist or set to False.

    Args:
        path (str): directory to begin the recursive search from, or module
            to run.

    Returns:
        list. all discovered tests.
    """
    path = os.path.abspath(path)
    tests_loader = loader.defaultTestLoader
    tests_loader.suiteClass = list
    tests_loader.loadTestsFromTestCase = lambda test: test

    if os.path.isdir(path):
        start_dir = path
        pattern = '*.py'

    else:
        start_dir = os.path.dirname(path)
        pattern = os.path.basename(path)

    discovered_tests = tests_loader.discover(start_dir, pattern, None)

    all_tests = []
    for test_class in chain(*discovered_tests):
        if not isinstance(test_class, type):
            continue

        if issubclass(test_class, (TestCase, TestFlow)) and \
                test_class not in (TestCase, TestFlow) and \
                getattr(test_class, "__test__", True) is True:

            all_tests.append(test_class)

    return all_tests


def main():
    # Rotest admin script:
    argv = sys.argv[1:]
    if argv[0] == "server":
        del sys.argv[1]
        server_main()

    elif argv[0] == "run":
        tests = do_discover(argv[1])

        class AlmightySuite(TestSuite):
            components = tests

        runner.main(AlmightySuite)

    # Default option - pass control to django-admin:
    else:
        from django.core import management
        management.execute_from_command_line()


if __name__ == "__main__":
    main()
