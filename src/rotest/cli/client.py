"""Run tests in a module or directory.

Usage:
    rotest [<path>...] [options]

Options:
    -h,  --help
            Show help message and exit.
    --version
            Print version information and exit.
    -c <path>, --config <path>
            Test configuration file path.
    -s, --save-state
            Enable saving state of resources.
    -d <delta-iterations>, --delta <delta-iterations>
            Enable run of failed tests only - enter the number of times the
            failed tests should be run.
    -p <processes>, --processes <processes>
            Use multiprocess test runner - specify number of worker
            processes to be created.
    -o <outputs>, --outputs <outputs>
            Output handlers separated by comma.
    -f <query>, --filter <query>
            Run only tests that match the filter expression,
            e.g. 'Tag1* and not Tag13'.
    -n <name>, --name <name>
            Assign a name for current launch.
    -l, --list
            Print the tests hierarchy and quit.
    -F, --failfast
            Stop the run on first failure.
    -D, --debug
            Enter ipdb debug mode upon any test exception.
    -S, --skip-init
            Skip initialization and validation of resources.
    -r <query>, --resources <query>
            Specify resources to request by attributes,
            e.g. '-r res1.group=QA,res2.comment=CI'.
"""
# pylint: disable=unused-argument,cell-var-from-loop
# pylint: disable=too-many-arguments,too-many-locals,redefined-builtin
from __future__ import print_function
from __future__ import absolute_import
import sys
import inspect
import argparse
from itertools import chain

import django
import pkg_resources
from attrdict import AttrDict

from rotest.core import TestSuite
from rotest.common import core_log
from rotest.core.filter import match_tags
from rotest.core.utils.common import print_test_hierarchy
from rotest.core.result.result import get_result_handlers
from rotest.cli.discover import discover_tests_under_paths
from rotest.core.runner import (DEFAULT_CONFIG_PATH, parse_config_file,
                                update_resource_requests, run as rotest_runner,
                                parse_resource_identifiers)
import six


def parse_outputs_option(outputs):
    """Parse value from CLI and validate all outputs are valid.

    Args:
        outputs (str): value gotten from CLI, e.g. "dots,excel".

    Returns:
        set: set of all parsed output handlers.
    """
    if not outputs:
        return None

    requested_handlers = outputs.split(",")

    available_handlers = get_result_handlers()

    non_existing_handlers = set(requested_handlers) - set(available_handlers)

    if non_existing_handlers:
        raise ValueError("The following output handlers are not "
                         "existing: {}.\nAvailable options: {}.".format(
                              ", ".join(non_existing_handlers),
                              ", ".join(available_handlers)))

    return requested_handlers


def get_tags_by_class(test_class):
    return test_class.TAGS + [test_class.__name__]


def run_tests(test, config):
    if config.list:
        print_test_hierarchy(test, config.filter)
        return

    resource_identifiers = parse_resource_identifiers(config.resources)
    update_resource_requests(test, resource_identifiers)

    runs_data = rotest_runner(config=config,
                              test_class=test,
                              outputs=config.outputs,
                              run_name=config.run_name,
                              enable_debug=config.debug,
                              fail_fast=config.fail_fast,
                              skip_init=config.skip_init,
                              save_state=config.save_state,
                              processes_number=config.processes,
                              delta_iterations=config.delta_iterations)

    sys.exit(runs_data[-1].get_return_value())


def filter_valid_values(dictionary):
    """Filter only values which are not None.

    Args:
        dictionary (dict): the dictionary to be filtered.

    Returns:
        iterator: (key, value) tuples where the value isn't None.
    """
    return ((key, value)
            for key, value in six.iteritems(dictionary)
            if value is not None)


def create_client_options_parser():
    """Create option parser for running tests.

    Returns:
        argparse.ArgumentParser: parser for CLI options.
    """
    version = pkg_resources.get_distribution("rotest").version

    parser = argparse.ArgumentParser(
        description="Run tests in a module or directory.")

    parser.add_argument("paths", nargs="*", default=(".",))
    parser.add_argument("--version", action="version",
                        version="rotest {}".format(version))
    parser.add_argument("--config", "-c", dest="config_path", metavar="path",
                        default=DEFAULT_CONFIG_PATH,
                        help="Test configuration file path")
    parser.add_argument("--save-state", "-s", action="store_true",
                        help="Enable saving state of resources")
    parser.add_argument("--delta", "-d", dest="delta_iterations",
                        metavar="iterations", type=int,
                        help="Enable run of failed tests only - enter the "
                             "number of times the failed tests should be run.")
    parser.add_argument("--processes", "-p", metavar="number", type=int,
                        help="Use multiprocess test runner - specify number "
                             "of worker processes to be created")
    parser.add_argument("--outputs", "-o",
                        type=parse_outputs_option,
                        help="Output handlers separated by comma. Options: {}"
                        .format(", ".join(get_result_handlers())))
    parser.add_argument("--filter", "-f", metavar="query",
                        help="Run only tests that match the filter "
                             "expression, e.g. 'Tag1* and not Tag13'")
    parser.add_argument("--order", "-O",
                        type=lambda tags: tags.split(','),
                        help="Order discovered tests by these tags, "
                             "separated by comma, e.g. 'Tag1,Tag2'")
    parser.add_argument("--name", "-n", metavar="name",
                        dest="run_name",
                        help="Assign a name for current launch")
    parser.add_argument("--list", "-l", action="store_true",
                        help="Print the tests hierarchy and quit")
    parser.add_argument("--failfast", "-F", action="store_true",
                        dest="fail_fast",
                        help="Stop the run on first failure")
    parser.add_argument("--debug", "-D", action="store_true",
                        help="Enter ipdb debug mode upon any test exception")
    parser.add_argument("--skip-init", "-S", action="store_true",
                        help="Skip initialization and validation of resources")
    parser.add_argument("--resources", "-r", metavar="query",
                        help="Specify resources to request be attributes, "
                             "e.g. '-r res1.group=QA,res2.comment=CI'")

    for entry_point in \
            pkg_resources.iter_entry_points("rotest.cli_client_parsers"):
        core_log.debug("Applying entry point %s", entry_point.name)
        extension_parser = entry_point.load()
        extension_parser(parser)

    return parser


def main(*tests):
    """Run the given tests.

    Args:
        *tests: either suites or tests to be run.
    """
    django.setup()

    parser = create_client_options_parser()
    arguments = parser.parse_args()

    config = AttrDict(chain(
        six.iteritems(parse_config_file(DEFAULT_CONFIG_PATH)),
        six.iteritems(parse_config_file(arguments.config_path)),
        filter_valid_values(vars(arguments)),
    ))

    # In case we're called via 'python test.py ...'
    if not sys.argv[0].endswith("rotest"):
        main_module = inspect.getfile(__import__("__main__"))
        config.paths = (main_module,)

    if len(tests) == 0:
        tests = list(discover_tests_under_paths(config.paths))

    if config.filter is not None:
        tests = [test for test in tests
                 if match_tags(get_tags_by_class(test), config.filter)]

    for tag in reversed(config.order):
        tests.sort(
            reverse=True,
            key=lambda test_class: match_tags(get_tags_by_class(test_class),
                                              tag))

    for entry_point in \
            pkg_resources.iter_entry_points("rotest.cli_client_actions"):
        core_log.debug("Applying entry point %s", entry_point.name)
        extension_action = entry_point.load()
        extension_action(tests, config)

    if len(tests) == 0:
        print("No test was found")
        sys.exit(1)

    class AlmightySuite(TestSuite):
        components = tests

    run_tests(test=AlmightySuite, config=config)
