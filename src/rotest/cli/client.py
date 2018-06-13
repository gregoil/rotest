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
# pylint: disable=too-many-arguments,too-many-locals,redefined-builtin
from __future__ import print_function
import sys
import inspect
from itertools import chain

import docopt
import django
import pkg_resources
from attrdict import AttrDict

from rotest.core import TestSuite
from rotest.core.utils.common import print_test_hierarchy
from rotest.cli.discover import discover_tests_under_paths
from rotest.core.result.handlers.tags_handler import TagsHandler
from rotest.core.result.result import get_result_handler_options
from rotest.core.runner import (DEFAULT_CONFIG_PATH, parse_config_file,
                                update_resource_requests, run as rotest_runner,
                                parse_resource_identifiers)


def parse_outputs_option(outputs):
    """Parse value from CLI and validate all outputs are valid.

    Args:
        outputs (str): value gotten from CLI, e.g. "dots,excel".

    Returns:
        set: set of all parsed output handlers.
    """
    if not outputs:
        return None

    requested_handlers = set(outputs.split(","))

    available_handlers = set(get_result_handler_options())

    non_existing_handlers = requested_handlers - available_handlers

    if non_existing_handlers:
        raise ValueError("The following output handlers are not "
                         "existing: {}.\nAvailable options: {}.".format(
                              ", ".join(non_existing_handlers),
                              ", ".join(available_handlers)))

    return requested_handlers


def run_tests(test, save_state, delta_iterations, processes, outputs, filter,
              run_name, list, fail_fast, debug, skip_init, config_path,
              resources):
    if list:
        print_test_hierarchy(test, filter)
        return

    resource_identifiers = parse_resource_identifiers(resources)
    update_resource_requests(test, resource_identifiers)

    if filter:
        # Add a tags filtering handler.
        TagsHandler.TAGS_PATTERN = filter
        outputs.add('tags')

    runs_data = rotest_runner(config=config_path,
                              test_class=test,
                              outputs=outputs,
                              run_name=run_name,
                              enable_debug=debug,
                              fail_fast=fail_fast,
                              skip_init=skip_init,
                              save_state=save_state,
                              processes_number=processes,
                              delta_iterations=delta_iterations)

    sys.exit(runs_data[-1].get_return_value())


def filter_valid_values(dictionary):
    """Filter only values which are not None.

    Args:
        dictionary (dict): the dictionary to be filtered.

    Returns:
        iterator: (key, value) tuples where the value isn't None.
    """
    return ((key, value)
            for key, value in dictionary.iteritems()
            if value is not None)


def main(*tests):
    """Run the given tests.

    Args:
        *tests: either suites or tests to be run.
    """
    # Load django models before using the runner in tests.
    django.setup()

    if sys.argv[0].endswith("rotest"):
        argv = sys.argv[1:]
    else:
        argv = sys.argv

    version = pkg_resources.get_distribution("rotest").version
    arguments = docopt.docopt(__doc__, argv=argv, version=version)
    arguments = dict(paths=arguments["<path>"] or ["."],
                     config_path=arguments["--config"] or DEFAULT_CONFIG_PATH,
                     save_state=arguments["--save-state"],
                     delta_iterations=int(arguments["--delta"])
                                      if arguments["--delta"] is not None
                                      else None,
                     processes=int(arguments["--processes"])
                               if arguments["--processes"] is not None
                               else None,
                     outputs=parse_outputs_option(arguments["--outputs"]),
                     filter=arguments["--filter"],
                     run_name=arguments["--name"],
                     list=arguments["--list"],
                     fail_fast=arguments["--failfast"],
                     debug=arguments["--debug"],
                     skip_init=arguments["--skip-init"],
                     resources=arguments["--resources"])

    config = parse_config_file(arguments["config_path"])
    default_config = parse_config_file(DEFAULT_CONFIG_PATH)

    options = AttrDict(chain(
        default_config.items(),
        filter_valid_values(config),
        filter_valid_values(arguments),
    ))

    if not sys.argv[0].endswith("rotest") and len(tests) == 0:
        main_module = inspect.getfile(__import__("__main__"))
        options.paths = (main_module,)

    if len(tests) == 0:
        tests = discover_tests_under_paths(options.paths)

    if len(tests) == 0:
        print("No test was found at given paths: {}".format(
              ", ".join(options.paths)))
        sys.exit(1)

    class AlmightySuite(TestSuite):
        components = tests

    run_tests(test=AlmightySuite,
              save_state=options.save_state,
              delta_iterations=options.delta_iterations,
              processes=options.processes,
              outputs=set(options.outputs),
              filter=options.filter,
              run_name=options.run_name,
              list=options.list,
              fail_fast=options.fail_fast,
              debug=options.debug,
              skip_init=options.skip_init,
              config_path=options.config_path,
              resources=options.resources)
