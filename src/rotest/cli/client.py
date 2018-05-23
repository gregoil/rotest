# pylint: disable=too-many-arguments,too-many-locals,redefined-builtin
import os
import sys
import inspect

import click
import django

from rotest.core import TestSuite
from rotest.core.utils.common import print_test_hierarchy
from rotest.cli.discover import discover_tests_under_paths
from rotest.core.result.handlers.tags_handler import TagsHandler
from rotest.core.result.result import get_result_handler_options
from rotest.core.runner import (DEFAULT_CONFIG_PATH, parse_config_file,
                                update_resource_requests, run,
                                parse_resource_identifiers)


def output_option_parser(context, _parameter, value):
    """Parse the given CLI options for output handler.

    Args:
        context (click.Context): click context object.
        _parameter: unused click parameter name.
        value (str): given value in the CLI.

    Returns:
        set: requested output handler names.

    Raises:
        click.BadOptionUsage: if the user asked for non-existing handlers.
    """
    # CLI is more prioritized than what config file has set
    if value is not None:
        requested_handlers = set(value.split(","))
    else:
        requested_handlers = set(context.params["outputs"])

    available_handlers = set(get_result_handler_options())

    non_existing_handlers = requested_handlers - available_handlers

    if non_existing_handlers:
        raise click.BadOptionUsage(
            "The following output handlers are not existing: {}.\n"
            "Available options: {}.".format(
                ", ".join(non_existing_handlers),
                ", ".join(available_handlers)))

    return requested_handlers


def set_options_by_config(context, _parameter, config_path):
    """Set default CLI outputs based on the given configuration file.

    Args:
        context (click.Context): click context object.
        _parameter: unused click parameter name.
        config_path (str): given config file by the CLI.

    Returns:
        attrdict.AttrDict: configuration in a dict like object.
    """
    config = parse_config_file(config_path)

    for key, value in config.items():
        context.params[key] = value

    return config_path


def run_tests(paths, save_state, delta_iterations, processes, outputs, filter,
              run_name, list, fail_fast, debug, skip_init, config_path,
              resources):
    tests = discover_tests_under_paths(paths)

    if len(tests) == 0:
        click.secho("No test was found at given paths", bold=True)
        sys.exit(1)

    class AlmightySuite(TestSuite):
        components = tests

    if list:
        print_test_hierarchy(AlmightySuite, filter)
        return

    resource_identifiers = parse_resource_identifiers(resources)
    update_resource_requests(AlmightySuite, resource_identifiers)

    if filter:
        # Add a tags filtering handler.
        TagsHandler.TAGS_PATTERN = filter
        outputs.add('tags')

    runs_data = run(config=config_path,
                    test_class=AlmightySuite,
                    outputs=outputs,
                    run_name=run_name,
                    enable_debug=debug,
                    fail_fast=fail_fast,
                    skip_init=skip_init,
                    save_state=save_state,
                    processes_number=processes,
                    delta_iterations=delta_iterations)

    sys.exit(runs_data[-1].get_return_value())


@click.command(
    help="Run tests in a module or directory.",
    context_settings=dict(
        help_option_names=['-h', '--help'],
    )
)
@click.argument("paths",
                type=click.Path(exists=True),
                nargs=-1)
@click.option("config_path",
              "--config-path", "--config", "-c",
              is_eager=True,
              default=DEFAULT_CONFIG_PATH,
              type=click.Path(exists=True),
              callback=set_options_by_config,
              help="Test configuration file path.")
@click.option("--save-state", "-s",
              is_flag=True,
              help="Enable saving state of resources.")
@click.option("delta_iterations",
              "--delta-iterations", "--delta", "-d",
              type=int,
              help="Enable run of failed tests only, enter the "
                   "number of times the failed tests should be run.")
@click.option("--processes", "-p",
              type=int,
              help="Use multiprocess test runner. "
                   "Specify number of worker processes to be created.")
@click.option("--outputs", "-o",
              callback=output_option_parser,
              help="Output handlers separated by comma. Options: {}."
              .format(", ".join(get_result_handler_options())))
@click.option("--filter", "-f",
              help="Run only tests that match the filter expression, "
                   "e.g 'Tag1* and not Tag13'.")
@click.option("run_name",
              "--name", "-n",
              help="Assign a name for the current run.")
@click.option("--list", "-l",
              is_flag=True,
              help="Print the tests hierarchy and quit.")
@click.option("fail_fast",
              "--failfast", "-F",
              is_flag=True,
              help="Stop the run on first failure.")
@click.option("--debug", "-D",
              is_flag=True,
              help="Enter ipdb debug mode upon any test exception.")
@click.option("--skip-init", "-S",
              is_flag=True,
              help="Skip initialization & validation of resources.")
@click.option("--resources", "-r",
              help="Specify resources to request by attributes, e.g.: "
                   "'-r res1.group=QA,res2.comment=CI'.")
def main(paths, **kwargs):
    django.setup()

    if "rotest run" not in click.get_current_context().command_path:
        # If this function is called from within a file, find tests in it
        paths = [inspect.getfile(__import__("__main__"))]

    else:
        # The user ran "rotest run"
        paths = paths or ["."]

    run_tests(paths, **kwargs)
