# pylint: disable=protected-access
from __future__ import absolute_import
import os
import unittest
from fnmatch import fnmatch
from collections import OrderedDict

import py

from rotest.common import core_log
from rotest.core.case import TestCase
from rotest.core.flow import TestFlow
from rotest.common.config import DISCOVERER_BLACKLIST


WHITE_LIST = ["*.py"]


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
            ("__test__" not in test.__dict__ or getattr(test, "__test__")))


def get_test_files(paths):
    """Return test files that match whitelist and blacklist patterns.

    Args:
        paths (iterable): list of filesystem paths to be looked recursively.

    Yields:
        str: path of test file.
    """
    for path in paths:
        path = os.path.abspath(path)
        filename = os.path.basename(path)

        if any(fnmatch(path, pattern) or fnmatch(filename, pattern)
               for pattern in DISCOVERER_BLACKLIST):
            continue

        if os.path.isfile(path):
            if not any(fnmatch(filename, pattern) for pattern in WHITE_LIST):
                continue

            yield path

        else:
            sub_files = (os.path.join(path, filename)
                         for filename in os.listdir(path))

            for sub_file in get_test_files(sub_files):
                yield sub_file


def discover_tests_under_paths(paths):
    """Search recursively for every test class under the given paths.

    Args:
        paths (iterable): list of filesystem paths to be searched.

    Returns:
        set: all discovered tests.
    """
    loader = unittest.TestLoader()
    loader.suiteClass = list
    loader.loadTestsFromTestCase = lambda test: test

    tests = OrderedDict()

    for path in get_test_files(paths):
        core_log.debug("Discovering tests in %s", path)

        module = py.path.local(path).pyimport()
        tests_discovered = loader.loadTestsFromModule(module)
        tests_discovered = {test: test
                            for test in tests_discovered
                            if is_test_class(test)}

        core_log.debug("Discovered %d tests in %s",
                       len(tests_discovered), path)
        tests.update(tests_discovered)

    return list(tests.values())
