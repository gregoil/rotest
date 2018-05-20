import mock
import click
from click.testing import CliRunner
import pytest
from pyfakefs.fake_filesystem_unittest import Patcher

from rotest.core import TestCase
from rotest.core.runner import DEFAULT_SCHEMA_PATH, DEFAULT_CONFIG_PATH
from rotest.cli.client import (output_option_parser,
                               set_options_by_config, main)


def test_getting_cli_value_in_output_parser():
    outputs = output_option_parser(mock.MagicMock(), "", "pretty,xml")
    assert set(outputs) == {"pretty", "xml"}


def test_getting_config_value_in_output_parser():
    outputs = output_option_parser(
        mock.MagicMock(params={"outputs": ["pretty", "xml"]}),
        "",
        None)
    assert set(outputs) == {"pretty", "xml"}


def test_bad_option_in_output_parser():
    with pytest.raises(click.BadOptionUsage,
                       match="The following output handlers are not existing: "
                             "asd.\nAvailable options:.*pretty"):
        output_option_parser(mock.MagicMock(), "", "pretty,asd")


def test_setting_options_by_config():
    context = mock.MagicMock(params={})
    with Patcher() as patcher:
        patcher.fs.add_real_file(source_path=DEFAULT_SCHEMA_PATH,
                                 target_path=DEFAULT_SCHEMA_PATH)
        patcher.fs.create_file(
            "config.json",
            contents="""
            {"debug": true,
             "processes": 2}
            """)
        set_options_by_config(context,
                              "",
                              "config.json")

    assert context.params == {"debug": True,
                              "processes": 2}


@mock.patch("rotest.cli.client.run_tests")
@mock.patch("inspect.getfile", mock.MagicMock(return_value="some_path"))
def test_finding_tests_in_current_module(run_tests):
    runner = CliRunner()
    runner.invoke(main, [])

    run_tests.assert_called_once_with(
        ["some_path"], config_path=DEFAULT_CONFIG_PATH, debug=False,
        delta_iterations=None, fail_fast=False, filter=None, list=False,
        outputs=["excel", "pretty"], processes=None, resources=None,
        run_name=None, save_state=False, skip_init=False)


@mock.patch("rotest.cli.client.run_tests")
@mock.patch(
    "click.get_current_context",
    mock.MagicMock(return_value=mock.MagicMock(command_path="rotest run")))
def test_finding_tests_in_current_directory(run_tests):
    runner = CliRunner()
    runner.invoke(main, [])

    run_tests.assert_called_once_with(
        ["."], config_path=DEFAULT_CONFIG_PATH, debug=False,
        delta_iterations=None, fail_fast=False, filter=None, list=False,
        outputs=["excel", "pretty"], processes=None, resources=None,
        run_name=None, save_state=False, skip_init=False)


def test_giving_invalid_paths():
    runner = CliRunner()
    result = runner.invoke(main, ["some_test.py"])

    assert result != 0
    assert 'Path "some_test.py" does not exist' in result.output


@mock.patch(
    "click.get_current_context",
    mock.MagicMock(return_value=mock.MagicMock(command_path="rotest run")))
@mock.patch("rotest.cli.client.discover_tests_under_paths",
            mock.MagicMock(return_value=set()))
def test_finding_no_test():
    with Patcher() as patcher:
        patcher.fs.add_real_file(source_path=DEFAULT_CONFIG_PATH,
                                 target_path=DEFAULT_CONFIG_PATH)
        patcher.fs.add_real_file(source_path=DEFAULT_SCHEMA_PATH,
                                 target_path=DEFAULT_SCHEMA_PATH)
        patcher.fs.create_file("some_test.py")

        runner = CliRunner()
        result = runner.invoke(main, ["some_test.py"])

    assert "No test was found at given paths" in result.output
    assert result.exit_code == 1


@mock.patch(
    "click.get_current_context",
    mock.MagicMock(return_value=mock.MagicMock(command_path="rotest run")))
def test_listing_tests():
    class Case(TestCase):
        def test_something(self):
            pass

    with Patcher() as patcher:
        patcher.fs.add_real_file(source_path=DEFAULT_CONFIG_PATH,
                                 target_path=DEFAULT_CONFIG_PATH)
        patcher.fs.add_real_file(source_path=DEFAULT_SCHEMA_PATH,
                                 target_path=DEFAULT_SCHEMA_PATH)
        patcher.fs.create_file("some_test.py")

        with mock.patch("rotest.cli.client.discover_tests_under_paths") \
                as tests:
            tests.return_value = {Case}

            runner = CliRunner()
            result = runner.invoke(main, ["some_test.py", "--list"])

    assert "Case.test_something" in result.output
    assert result.exit_code == 0
