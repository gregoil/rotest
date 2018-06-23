import sys

import mock
import pytest
from termcolor import colored
from pyfakefs.fake_filesystem_unittest import Patcher

from rotest.cli.main import main
from rotest.core import TestCase
from rotest.common.constants import MAGENTA
from rotest.cli.client import main as client_main
from rotest.cli.client import parse_outputs_option
from rotest.core.runner import DEFAULT_SCHEMA_PATH, DEFAULT_CONFIG_PATH


def test_parsing_output_handlers():
    outputs = parse_outputs_option("pretty,xml,excel")
    assert outputs == {"pretty", "xml", "excel"}


def test_bad_option_in_output_parser():
    with pytest.raises(ValueError,
                       match="The following output handlers are not existing: "
                             "asd.\nAvailable options:.*pretty"):
        parse_outputs_option("pretty,asd")


@mock.patch("rotest.cli.client.run_tests")
@mock.patch("rotest.cli.client.discover_tests_under_paths",
            mock.MagicMock(return_value=["test"]))
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
                 "filter": "some filter",
                 "run_name": "some name",
                 "resources": "query"}
            """)

        sys.argv = ["rotest", "--config", "config.json"]
        main()

    run_tests.assert_called_once_with(
        config_path="config.json",
        delta_iterations=5, processes=2, outputs={"xml", "remote"},
        filter="some filter", run_name="some name", resources="query",
        debug=False, fail_fast=False, list=False, save_state=False,
        skip_init=False, test=mock.ANY
    )


@mock.patch("rotest.cli.client.run_tests")
@mock.patch("rotest.cli.client.discover_tests_under_paths",
            mock.MagicMock(return_value=["test"]))
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
                    "-f", "other filter", "-n", "other name",
                    "-r", "other query", "-D", "-F", "-l", "-s", "-S"]
        main()

    run_tests.assert_called_once_with(
        config_path="config.json",
        delta_iterations=4, processes=1, outputs={"pretty", "full"},
        filter="other filter", run_name="other name", resources="other query",
        debug=True, fail_fast=True, list=True, save_state=True,
        skip_init=True, test=mock.ANY
    )


@mock.patch("inspect.getfile", mock.MagicMock(return_value="script"))
@mock.patch("rotest.cli.client.run_tests")
@mock.patch("rotest.cli.client.discover_tests_under_paths",
            return_value=["test"])
def test_finding_tests_in_current_module(discover, run_tests):
    sys.argv = ["python", "script.py"]
    main()

    discover.assert_called_once_with(("script",))
    run_tests.assert_called_once_with(
        test=mock.ANY, config_path=DEFAULT_CONFIG_PATH, debug=False,
        delta_iterations=0, fail_fast=False, filter=None, list=False,
        outputs={"excel", "pretty"}, processes=None, resources=None,
        run_name=None, save_state=False, skip_init=False)


@mock.patch("rotest.cli.client.run_tests")
@mock.patch("rotest.cli.client.discover_tests_under_paths",
            return_value=["test"])
def test_finding_tests_in_current_directory(discover, run_tests):
    sys.argv = ["rotest"]
    main()

    discover.assert_called_once_with((".",))
    run_tests.assert_called_once_with(
        test=mock.ANY, config_path=DEFAULT_CONFIG_PATH, debug=False,
        delta_iterations=0, fail_fast=False, filter=None, list=False,
        outputs={"excel", "pretty"}, processes=None, resources=None,
        run_name=None, save_state=False, skip_init=False)


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


def test_listing_and_filtering_given_tests(capsys):
    class Case1(TestCase):
        def test_first(self):
            pass

    class Case2(TestCase):
        def test_second(self):
            pass

    sys.argv = ["python", "some_test.py", "--list", "--filter", "Case1"]
    client_main(Case1, Case2)

    out, _ = capsys.readouterr()
    assert colored(" |   Case1.test_first []", MAGENTA) in out
    assert colored(" |   Case2.test_second []", MAGENTA) not in out


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
        assert "No test was found at given paths:" in out


def test_listing_tests(capsys):
    class Case(TestCase):
        def test_something(self):
            pass

    with Patcher() as patcher:
        patcher.fs.add_real_file(DEFAULT_CONFIG_PATH)
        patcher.fs.add_real_file(DEFAULT_SCHEMA_PATH)
        patcher.fs.create_file("some_test.py")

        with mock.patch("rotest.cli.client.discover_tests_under_paths",
                        return_value={Case}):
            sys.argv = ["rotest", "some_test.py", "--list"]

            main()
            out, _ = capsys.readouterr()
            assert "Case.test_something" in out
