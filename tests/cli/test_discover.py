import unittest

import mock
import pytest
from pyfakefs.fake_filesystem_unittest import Patcher

from rotest.core import TestSuite, TestCase, TestBlock
from rotest.cli.discover import (is_test_class, guess_root_dir,
                                 get_test_files, discover_tests_under_paths)


def jtest_instance_is_not_test_class():
    assert not is_test_class(1)


def test_non_case_or_flow_are_not_test_classes():
    assert not is_test_class(unittest.TestCase)
    assert not is_test_class(TestSuite)
    assert not is_test_class(TestBlock)


def test_abstract_tests_are_not_test_classes():
    assert not is_test_class(TestCase)

    from rotest.core import TestFlow
    assert not is_test_class(TestFlow)


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


@mock.patch("rotest.common.config")
@mock.patch("os.curdir")
def test_guess_root_dir_when_config_is_absent(current_dir, config):
    config.config_path = None
    assert guess_root_dir() == current_dir


@mock.patch("rotest.common.config")
def test_guess_root_dir_when_config_exists(config):
    config.config_path = "path/to/root/rotest.yml"
    assert guess_root_dir() == "path/to/root"


def test_yielding_test_files():
    with Patcher() as patcher:
        patcher.fs.create_dir("root")
        patcher.fs.create_file("root/test_something.py")
        patcher.fs.create_file("root/some_test.py")

        assert set(get_test_files(["root"])) == {"/root/test_something.py",
                                                 "/root/some_test.py"}


def test_skipping_files_by_whitelist():
    with Patcher() as patcher:
        patcher.fs.create_dir("root")
        patcher.fs.create_file("root/some_file.py")

        assert set(get_test_files(["root"])) == set()


def test_skipping_files_by_blacklist():
    with Patcher() as patcher:
        patcher.fs.create_dir("root")
        patcher.fs.create_dir("root/.git")
        patcher.fs.create_file("root/.git/test_something.py")

        assert set(get_test_files(["root"])) == set()


@mock.patch("unittest.TestLoader")
@mock.patch("rotest.cli.discover.get_test_files",
            return_value=["some_test.py"])
def test_discovering_tests(_get_test_files_mock, loader_mock):
    class Case(TestCase):
        def test(self):
            pass

    loader_mock.return_value.loadTestsFromName.return_value = [Case]

    with mock.patch("__builtin__.__import__"):
        assert discover_tests_under_paths(["some_test.py"]) == {Case}


def test_importing_bad_file():
    with Patcher() as patcher:
        patcher.fs.create_file("some_bad_test.py")

        with pytest.raises(ImportError), \
                mock.patch("__builtin__.__import__",
                           side_effect=ImportError):
            discover_tests_under_paths(["some_bad_test.py"])
