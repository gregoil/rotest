# pylint: disable=protected-access
import os
import unittest
from itertools import chain

from isort.pie_slice import OrderedSet

from rotest.core import TestCase, TestFlow
from rotest.common.config import config_path


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


def guess_root_dir():
    """Guess the root directory of the project.

    Returns:
        str: directory containing the rotest configuration file if it exists,
            the current directory otherwise.
    """
    if config_path is not None:
        return os.path.dirname(config_path)

    return os.curdir


def discover_tests_under_paths(paths):
    """Search recursively for every test class under the given paths.

    Args:
        paths (iterable): list of filesystem paths to be searched.

    Returns:
        set: all discovered tests.
    """
    loader = unittest.TestLoader()

    loader._top_level_dir = guess_root_dir()
    loader.suiteClass = list
    loader.loadTestsFromTestCase = lambda test: test

    tests = OrderedSet()

    for path in paths:
        path = os.path.abspath(path)
        if os.path.isdir(path):
            tests_discovered = chain(*loader.discover(start_dir=path,
                                                      pattern="*.py"))

        else:  # It's a file
            module_name = loader._get_name_from_path(path)
            tests_discovered = loader.loadTestsFromName(module_name)

        tests.update(test for test in tests_discovered if is_test_class(test))

    return tests
