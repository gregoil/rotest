import os
import unittest

import mock
import pytest
from pyfakefs.fake_filesystem_unittest import Patcher

from rotest.core import TestSuite, TestCase, TestBlock
from rotest.cli.discover import (is_test_class,
                                 get_test_files, discover_tests_under_paths)


def test_instance_is_not_test_class():
    assert not is_test_class(1)


def test_non_case_or_flow_are_not_test_classes():
    assert not is_test_class(unittest.TestCase)
    assert not is_test_class(TestSuite)
    assert not is_test_class(TestBlock)


def test_abstract_tests_are_not_test_classes():
    assert not is_test_class(TestCase)


def test_dunderscore_test_attribute():
    class SimpleCase(TestCase):
        pass

    class AbstractCase(TestCase):
        __test__ = False

    class NonAbstractCase(TestCase):
        __test__ = True

    assert is_test_class(SimpleCase)
    assert not is_test_class(AbstractCase)
    assert is_test_class(NonAbstractCase)


def test_yielding_test_files():
    with Patcher() as patcher:
        patcher.fs.create_dir("root")
        patcher.fs.create_file(os.path.join("root", "test_something.py"))
        patcher.fs.create_file(os.path.join("root", "some_test.py"))

        sub_files = {os.path.join(os.sep, "root", "test_something.py"),
                     os.path.join(os.sep, "root", "some_test.py")}

        assert set(get_test_files(["root"])) == sub_files


def test_skipping_files_by_whitelist():
    with Patcher() as patcher:
        patcher.fs.create_dir("root")
        patcher.fs.create_file("root/some_file.txt")

        assert set(get_test_files(["root"])) == set()


def test_skipping_files_by_blacklist():
    with Patcher() as patcher:
        patcher.fs.create_dir("root")
        patcher.fs.create_dir("root/.git")
        patcher.fs.create_file("root/.git/test_something.py")

        assert set(get_test_files(["root"])) == set()


@mock.patch("rotest.cli.discover.get_test_files",
            mock.MagicMock(return_value=["some_test.py"]))
@mock.patch("unittest.TestLoader")
@mock.patch("py.path", mock.MagicMock())
def test_discovering_tests(loader_mock):
    class Case(TestCase):
        def test(self):
            pass

    loader_mock.return_value.loadTestsFromModule.return_value = [Case]

    with mock.patch("__builtin__.__import__"):
        assert discover_tests_under_paths(["some_test.py"]) == {Case}


def test_importing_bad_file():
    with Patcher() as patcher:
        patcher.fs.create_file("some_bad_test.py")

        with pytest.raises(ImportError):
            with mock.patch("__builtin__.__import__",
                            side_effect=ImportError):
                discover_tests_under_paths(["some_bad_test.py"])
