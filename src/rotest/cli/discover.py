import os
import unittest
from itertools import chain

from isort.pie_slice import OrderedSet

from rotest.core import TestCase, TestFlow


def is_test_class(test):
    """Return if the provided object is a runnable test.

    Args:
        test (object): the object to be inspected.

    Returns:
        bool: whether it's either TestCase or TestFlow, and should be ran.
    """
    return (isinstance(test, type) and
            issubclass(test, (TestCase, TestFlow)) and
            test not in (TestFlow, TestCase) and
            getattr(test, "__test__", True))


def discover_tests_under_paths(paths):
    """Search recursively for every test class under the given paths.

    Args:
        paths (iterable): list of filesystem paths to be searched.

    Returns:
        set: all discovered tests.
    """
    loader = unittest.defaultTestLoader
    loader.suiteClass = list
    loader.loadTestsFromTestCase = lambda test: test

    tests = OrderedSet()

    for path in paths:
        path = os.path.abspath(path)
        if os.path.isdir(path):
            tests_discovered = chain(*loader.discover(start_dir=path,
                                                      pattern="*.py"))

        else:  # It's a file
            _, file_name = os.path.split(path)
            module_name, _ = os.path.splitext(file_name)
            tests_discovered = loader.loadTestsFromName(module_name)

        tests.update(test for test in tests_discovered if is_test_class(test))

    return tests
