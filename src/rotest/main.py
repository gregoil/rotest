#!/usr/bin/env python
import sys
from itertools import chain


def do_discover(start_dir):
    from unittest import loader
    from rotest.core import TestCase, TestFlow
    tests_loader = loader.defaultTestLoader

    def loadTestsFromTestCase(testCaseClass):
        return testCaseClass

    tests_loader.suiteClass = list
    tests_loader.loadTestsFromTestCase = loadTestsFromTestCase
    discovered_tests = tests_loader.discover(start_dir, '*.py', start_dir)

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
        from rotest.management.server.main import main
        main()

    elif argv[0] == "discover":
        tests = do_discover(argv[1])
        from rotest.core import TestSuite, runner
        class AlmightySuite(TestSuite):
            components = tests

        del argv[1:3]
        runner.main(AlmightySuite)


    # Default option - pass control to django-admin:
    else:
        from django.core import management
        management.execute_from_command_line()


if __name__ == "__main__":
    main()
