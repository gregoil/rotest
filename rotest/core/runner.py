"""Describes Rotest's test running handler class."""
# pylint: disable=dangerous-default-value,protected-access
# pylint: disable=expression-not-assigned,too-many-arguments
# pylint: disable=invalid-name,too-few-public-methods,no-member,unused-argument
import os
import sys
import optparse

import django

from rotest.common import core_log
from rotest.core.result.result import Result
from rotest.core.utils.json_parser import parse
from rotest.core.utils.common import print_test_hierarchy
from rotest.core.runners.base_runner import BaseTestRunner
from rotest.core.result.handlers.tags_handler import TagsHandler
from rotest.core.runners.multiprocess.manager.runner import MultiprocessRunner


LAST_RUN_INDEX = -1
MINIMUM_TIMES_TO_RUN = 1
FILE_FOLDER = os.path.dirname(__file__)
DEFAULT_SCHEMA_PATH = os.path.join(FILE_FOLDER, "schema.json")
DEFAULT_CONFIG_PATH = os.path.join(FILE_FOLDER, "default_config.json")

OUTPUTS_OPTIONS = Result.OUTPUTS_HANDLERS.keys()
OUTPUTS_OPTIONS.remove(TagsHandler.NAME)

# Load django models before using the runner in tests.
django.setup()


def get_runner(save_state=False, outputs=None, config=None,
               processes_number=None, run_delta=False, run_name=None,
               fail_fast=False, enable_debug=False, skip_init=None,
               stream=sys.stderr):
    """Return a test runner instance.

    Args:
        save_state (bool): determine if storing resources state is required.
            The behavior can be overridden using resource's save_state flag.
        outputs (list): list of the required output handlers' names.
        config (object): config object, will be transfered to each test.
        run_delta (bool): determine whether to run only tests that failed the
            last run (according to the results DB).
        processes_number (number): number of multiprocess runner's worker
            processes, None means that a regular runner will be used.
        run_name (str): name of the current run.
        fail_fast (bool): whether to stop the run on the first failure.
        enable_debug (bool): whether to enable entering ipdb debugging mode
            upon any exception in a test statement.
        skip_init (bool): True to skip resources initialize and validation.
        stream (file): output stream.

    Returns:
        runner. test runner instance.
    """
    if processes_number is not None and processes_number > 0:
        if enable_debug is True:
            raise RuntimeError("Cannot debug in multiprocess")

        return MultiprocessRunner(stream=stream,
                                  config=config,
                                  outputs=outputs,
                                  run_name=run_name,
                                  failfast=fail_fast,
                                  enable_debug=False,
                                  skip_init=skip_init,
                                  run_delta=run_delta,
                                  save_state=save_state,
                                  workers_number=processes_number)

    return BaseTestRunner(stream=stream,
                          config=config,
                          outputs=outputs,
                          run_name=run_name,
                          failfast=fail_fast,
                          run_delta=run_delta,
                          skip_init=skip_init,
                          save_state=save_state,
                          enable_debug=enable_debug)


def run(test_class, save_state=None, outputs=None, config=None,
        processes_number=None, delta_iterations=None, run_name=None,
        fail_fast=None, enable_debug=None, skip_init=None):
    """Return a test runner instance.

    Args:
        test_class (type): test class inheriting from
            :class:`rotest.core.case.TestCase` or
            :class:`rotest.core.suite.TestSuite`.
        save_state (bool): determine if storing resources state is required.
            The behavior can be overridden using resource's save_state flag.
        outputs (list): list of the required output handlers' names.
        config (object): config object, will be transfered to each test.
        processes_number (number): number of multiprocess runner's worker
            processes, None means that a regular runner will be used.
        delta_iterations (number): determine whether to run only tests that
            failed the last run (according to the results DB), and how many
            times to do so. If delta_iterations = 0, the tests will run
            normally. If delta_iterations = 1, the 'delta-tests' will be run
            once. If delta_iterations > 1, the 'delta-tests' will run
            delta_iterations times.
        run_name (str): name of the current run.
        fail_fast (bool): whether to stop the run on the first failure.
        enable_debug (bool): whether to enable entering ipdb debugging mode
            upon any exception in a test statement.
        skip_init (bool): True to skip resources initialization and validation.

    Returns:
        list. list of RunData of the test runs.
    """
    times_to_run = max(delta_iterations, MINIMUM_TIMES_TO_RUN)

    runs_data = []
    test_runner = get_runner(config=config,
                             outputs=outputs,
                             run_name=run_name,
                             fail_fast=fail_fast,
                             skip_init=skip_init,
                             save_state=save_state,
                             enable_debug=enable_debug,
                             run_delta=bool(delta_iterations),
                             processes_number=processes_number)

    for _ in xrange(times_to_run):
        runs_data.append(test_runner.run(test_class))

    return runs_data


def output_option_parser(option, opt, value, parser):
    """Parse the string of outputs and validate it.

    Args:
        option (optparse.Option): the Option instnace.
        opt (str): option calling format.
        value (str): user input for the option.
        parser (optparse.OptionParser): the parser of the option.

    Raises:
        optparse.OptionValueError. unsupported handler requested.
    """
    output_options = OUTPUTS_OPTIONS

    handlers = value.split(',')

    for handler in handlers:
        if handler not in output_options:
            raise optparse.OptionValueError('unsupported handler %r, '
                                            'supported handlers %r' %
                                            (handler, output_options))

    setattr(parser.values, option.dest, handlers)


def _parse_config_file(json_path, schema_path=DEFAULT_SCHEMA_PATH):
    """Parse configuration file to create the config dictionary.

    Args:
        json_path (str): path to the json config file.
        schema_path (str): path of the schema file - optional.

    Returns:
        AttrDict. configuration dict, containing default values for run
            options and other parameters.
    """
    if os.path.exists(json_path) is False:
        raise ValueError("Illegal config-path: %r" % json_path)

    core_log.debug('Parsing configuration file %r', json_path)
    config = parse(json_path=json_path,
                   schema_path=schema_path)

    return config


def set_run_configuration(options, schema_path=DEFAULT_SCHEMA_PATH):
    """Update options according to the default configuration and the given.

    This function firstly loads the default configuration file (found in the
    rotest files dir), and then, if given, updates it by the user config file
    (replacing values of the default configuration if present).

    Args:
        options (optparse.Values): options value object to update.
        schema_path (str): path of the schema file - optional.

    Returns:
        AttrDict. configuration dict, containing default values for run
            options and other parameters.

    Note:
        Command line parameters always override configuration values if given.
    """
    # Load default configuration
    config = _parse_config_file(DEFAULT_CONFIG_PATH,
                                schema_path=DEFAULT_SCHEMA_PATH)

    if options.config_path is not None:
        config.update(_parse_config_file(options.config_path,
                                         schema_path=schema_path))

    # Update options according to the configurations
    for option_name, option_value in config.iteritems():
        cmd_value = getattr(options, option_name, None)
        if cmd_value is None:
            setattr(options, option_name, option_value)

        else:
            setattr(config, option_name, cmd_value)

    return config


def main(test_class, save_state=None, delta_iterations=None, processes=None,
         outputs=None, test_filter=None, config_path=None, skip_init=None):
    """Call the Rotest's `run` method using the given options.

    Args:
        test_class (type): test class inheriting from
            :class:`rotest.core.case.TestCase` or
            :class:`rotest.core.suite.TestSuite`.
        save_state (bool): enable save state.
        delta_iterations (number): enable run of failed tests only, enter the
            number of times the failed tests should run.
        processes (number): use multiprocess test runner.
        outputs (str): output handlers separated by comma.
        test_filter (str): trim test by a given filter to contain only tags
            matching tests.
        skip_init (bool): True to skip resources initialize and validation.

    Raises:
        SystemExit. exit with a status matching the test result.
    """
    parser = optparse.OptionParser()

    parser.add_option("-c", "--config-path", action="store",
                      default=config_path, type="string", dest="config_path",
                      help="Tests' configuration file path")

    parser.add_option("-s", "--save-state", action="store_true",
                      default=save_state, help="Enable save state",
                      dest="save_state")

    parser.add_option("-d", "--delta-iterations", action="store", type="int",
                      default=delta_iterations, help="Enable run of failed "
                      "tests only, enter the number of times the failed tests "
                      "should run", dest="delta_iterations")

    parser.add_option("-p", "--processes", action="store", type='int',
                      default=processes, help="Use multiprocess test runner",
                      dest="processes")

    parser.add_option("-o", "--outputs", type='string',
                      help="Output handlers separated by comma, "
                      "options %r" % str(OUTPUTS_OPTIONS), action="callback",
                      callback=output_option_parser, dest="outputs",
                      default=outputs)

    parser.add_option("-f", "--filter", action="store", type="str",
                      default=test_filter, help='Run only tests that match '
                      'the filter expression, e.g "Tag1* and not Tag13"',
                      dest="filter")

    parser.add_option("-n", "--name", action="store", type='string',
                      default=None, help="Assign run name", dest="run_name")

    parser.add_option("-l", "--list", action="store_true",
                      help="Print the tests hierarchy and quit", dest="list")

    parser.add_option("-F", "--failfast", action="store_true",
                      help="Stop the run on first failure", dest="fail_fast")

    parser.add_option("-D", "--debug", action="store_true",
                      help="Enter ipdb debug mode upon any test exception",
                      dest="debug")

    parser.add_option("-S", "--skip-init", action="store_true",
                      default=skip_init, help="Skip initialization and "
                      "validation of resources", dest="skip_init")

    options, _ = parser.parse_args()

    config = set_run_configuration(options)

    if options.list is True:
        print_test_hierarchy(test_class, options.filter)
        return

    if options.filter is not None and options.filter != "":
        # Add a tags filtering handler.
        TagsHandler.TAGS_PATTERN = options.filter
        options.outputs.append('tags')

    runs_data = run(config=config,
                    test_class=test_class,
                    outputs=options.outputs,
                    run_name=options.run_name,
                    enable_debug=options.debug,
                    fail_fast=options.fail_fast,
                    skip_init=options.skip_init,
                    save_state=options.save_state,
                    processes_number=options.processes,
                    delta_iterations=options.delta_iterations)

    sys.exit(runs_data[LAST_RUN_INDEX].get_return_value())
