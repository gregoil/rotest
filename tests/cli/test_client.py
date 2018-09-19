import sys

import mock
import pytest
from attrdict import AttrDict
from pyfakefs.fake_filesystem_unittest import Patcher

from rotest.cli.main import main
from rotest.core import TestCase, TestSuite
from rotest.cli.client import main as client_main
from rotest.cli.client import parse_outputs_option
from rotest.core.runner import DEFAULT_SCHEMA_PATH, DEFAULT_CONFIG_PATH


class MockCase(TestCase):
    pass


def test_parsing_output_handlers():
    outputs = parse_outputs_option("pretty,xml,excel")
    assert set(outputs) == {"pretty", "xml", "excel"}


def test_bad_option_in_output_parser():
    with pytest.raises(ValueError,
                       match="The following output handlers are not existing: "
                             "asd.\nAvailable options:.*pretty"):
        parse_outputs_option("pretty,asd")


@mock.patch("rotest.cli.client.run_tests")
@mock.patch("rotest.cli.client.discover_tests_under_paths",
            mock.MagicMock(return_value={MockCase}))
def test_setting_options_by_config(run_tests):
    with Patcher() as patcher:
        patcher.fs.add_real_file(DEFAULT_SCHEMA_PATH)
        patcher.fs.add_real_file(DEFAULT_CONFIG_PATH)
        patcher.fs.create_file(
            "config.json",
            contents="""
                {"delta_iterations": 5,
                 "processes": 2,
                 "outputs": ["xml", "remote"],
                 "filter": "MockCase",
                 "run_name": "some name",
                 "resources": "query"}
            """)

        sys.argv = ["rotest", "--config", "config.json"]
        main()

    config = AttrDict(delta_iterations=5, processes=2,
                      paths=(".",), config_path="config.json",
                      outputs=list({"xml", "remote"}), filter="MockCase",
                      run_name="some name", resources="query", debug=False,
                      fail_fast=False, list=False, save_state=False,
                      skip_init=False)

    run_tests.assert_called_once_with(config=config, test=mock.ANY)


@mock.patch("rotest.cli.client.run_tests")
@mock.patch("rotest.cli.client.discover_tests_under_paths",
            mock.MagicMock(return_value={MockCase}))
def test_setting_options_by_cli(run_tests):
    with Patcher() as patcher:
        patcher.fs.add_real_file(DEFAULT_SCHEMA_PATH)
        patcher.fs.add_real_file(DEFAULT_CONFIG_PATH)
        patcher.fs.create_file(
            "config.json",
            contents="""
                {"delta_iterations": 5,
                 "processes": 2,
                 "outputs": ["xml", "remote"],
                 "filter": "some filter",
                 "run_name": "some name",
                 "resources": "query"}
            """)

        sys.argv = ["rotest", "-c", "config.json",
                    "-d", "4", "-p", "1", "-o", "pretty,full",
                    "-f", "MockCase", "-n", "other name",
                    "-r", "other query", "-D", "-F", "-l", "-s", "-S"]
        main()

    config = AttrDict(delta_iterations=4, processes=1,
                      paths=(".",), config_path="config.json",
                      outputs=list({"pretty", "full"}), filter="MockCase",
                      run_name="other name", resources="other query",
                      debug=True, fail_fast=True, list=True, save_state=True,
                      skip_init=True)

    run_tests.assert_called_once_with(config=config, test=mock.ANY)


@mock.patch("inspect.getfile", mock.MagicMock(return_value="script.py"))
@mock.patch("rotest.cli.client.run_tests")
@mock.patch("rotest.cli.client.discover_tests_under_paths",
            return_value=["test"])
def test_finding_tests_in_current_module(discover, run_tests):
    sys.argv = ["python", "script.py"]
    main()

    discover.assert_called_once_with(("script.py",))
    run_tests.assert_called()


@mock.patch("rotest.cli.client.run_tests")
@mock.patch("rotest.cli.client.discover_tests_under_paths",
            return_value=["test"])
def test_finding_tests_in_current_directory(discover, run_tests):
    sys.argv = ["rotest"]
    main()

    discover.assert_called_once_with((".",))
    run_tests.assert_called()


def test_listing_given_tests(capsys):
    class Case1(TestCase):
        def test_first(self):
            pass

    class Case2(TestCase):
        def test_second(self):
            pass

    sys.argv = ["python", "some_test.py", "--list"]
    client_main(Case1, Case2)

    out, _ = capsys.readouterr()
    assert "Case1.test_first" in out
    assert "Case2.test_second" in out


def test_listing_and_filtering_given_tests_by_name(capsys):
    class Case1(TestCase):
        def test_first(self):
            pass

    class Case2(TestCase):
        def test_second(self):
            pass

    sys.argv = ["python", "some_test.py", "--list", "--filter", "Case1"]
    client_main(Case1, Case2)

    out, _ = capsys.readouterr()
    assert " |   Case1.test_first []" in out
    assert " |   Case2.test_second []" not in out


def test_listing_and_filtering_given_tests_by_tag(capsys):
    class Case1(TestCase):
        TAGS = ["Foo"]

        def test_first(self):
            pass

    class Case2(TestCase):
        TAGS = ["Bar"]

        def test_second(self):
            pass

    sys.argv = ["python", "some_test.py", "--list", "--filter", "Foo"]
    client_main(Case1, Case2)

    out, _ = capsys.readouterr()
    assert " |   Case1.test_first ['Foo']" in out
    assert " |   Case2.test_second ['Bar']" not in out


def test_giving_invalid_paths():
    sys.argv = ["rotest", "some_test.py"]
    with pytest.raises(OSError):
        main()


@mock.patch("rotest.cli.client.discover_tests_under_paths",
            mock.MagicMock(return_value=set()))
def test_finding_no_test(capsys):
    with Patcher() as patcher:
        patcher.fs.add_real_file(DEFAULT_CONFIG_PATH)
        patcher.fs.add_real_file(DEFAULT_SCHEMA_PATH)
        patcher.fs.create_file("some_test.py")

        sys.argv = ["rotest", "some_test.py"]
        with pytest.raises(SystemExit):
            main()

        out, _ = capsys.readouterr()
        assert "No test was found" in out


def test_discarding_all_tests(capsys):
    class Case1(TestCase):
        def test_something(self):
            pass

    class Case2(TestCase):
        def test_something(self):
            pass

    class MockSuite(TestSuite):
        components = [Case1, Case2]

    with Patcher() as patcher:
        patcher.fs.add_real_file(DEFAULT_CONFIG_PATH)
        patcher.fs.add_real_file(DEFAULT_SCHEMA_PATH)
        patcher.fs.create_file("some_test.py")

        with mock.patch("rotest.cli.client.discover_tests_under_paths",
                        return_value={MockSuite}):
            sys.argv = ["rotest", "some_test.py",
                        "--filter", "NOTHING",
                        "--list"]

            with pytest.raises(SystemExit):
                main()

            out, _ = capsys.readouterr()
            assert "No test was found" in out
            assert "Case1.test_something" not in out
            assert "Case2.test_something" not in out


def test_discarding_nothing_no_filter(capsys):
    class Case1(TestCase):
        def test_something(self):
            pass

    class Case2(TestCase):
        def test_something(self):
            pass

    class MockSuite(TestSuite):
        components = [Case1, Case2]

    with Patcher() as patcher:
        patcher.fs.add_real_file(DEFAULT_CONFIG_PATH)
        patcher.fs.add_real_file(DEFAULT_SCHEMA_PATH)
        patcher.fs.create_file("some_test.py")

        with mock.patch("rotest.cli.client.discover_tests_under_paths",
                        return_value={MockSuite}):
            sys.argv = ["rotest", "some_test.py", "--list"]

            main()
            out, _ = capsys.readouterr()
            assert "Case1.test_something" in out
            assert "Case2.test_something" in out


def test_discarding_nothing_star_filter(capsys):
    class Case1(TestCase):
        def test_something(self):
            pass

    class Case2(TestCase):
        def test_something(self):
            pass

    with Patcher() as patcher:
        patcher.fs.add_real_file(DEFAULT_CONFIG_PATH)
        patcher.fs.add_real_file(DEFAULT_SCHEMA_PATH)
        patcher.fs.create_file("some_test.py")

        with mock.patch("rotest.cli.client.discover_tests_under_paths",
                        return_value={Case1, Case2}):
            sys.argv = ["rotest", "some_test.py", "--filter", "*", "--list"]

            main()
            out, _ = capsys.readouterr()
            assert "Case1.test_something" in out
            assert "Case2.test_something" in out


def test_discarding_some_tests_by_name(capsys):
    class Case1(TestCase):
        def test_something(self):
            pass

    class Case2(TestCase):
        def test_something(self):
            pass

    with Patcher() as patcher:
        patcher.fs.add_real_file(DEFAULT_CONFIG_PATH)
        patcher.fs.add_real_file(DEFAULT_SCHEMA_PATH)
        patcher.fs.create_file("some_test.py")

        with mock.patch("rotest.cli.client.discover_tests_under_paths",
                        return_value={Case1, Case2}):
            sys.argv = ["rotest", "some_test.py",
                        "--filter", "Case2",
                        "--list"]

            main()
            out, _ = capsys.readouterr()
            assert "Case1.test_something" not in out
            assert "Case2.test_something" in out


def test_discarding_some_tests_by_tag(capsys):
    class Case1(TestCase):
        TAGS = ["HELLO"]

        def test_something(self):
            pass

    class Case2(TestCase):
        TAGS = ["WORLD"]

        def test_something(self):
            pass

    with Patcher() as patcher:
        patcher.fs.add_real_file(DEFAULT_CONFIG_PATH)
        patcher.fs.add_real_file(DEFAULT_SCHEMA_PATH)
        patcher.fs.create_file("some_test.py")

        with mock.patch("rotest.cli.client.discover_tests_under_paths",
                        return_value={Case1, Case2}):
            sys.argv = ["rotest", "some_test.py",
                        "--filter", "WORLD",
                        "--list"]

            main()
            out, _ = capsys.readouterr()
            assert "Case1.test_something" not in out
            assert "Case2.test_something" in out
