"""Managing configuration that comes from CLI, env-vars & config files."""
from __future__ import absolute_import

import os
import sys
import itertools

import yaml
from attrdict import AttrDict
from future.utils import iteritems
from future.builtins import zip, object

import six


ROTEST_CONFIGURATION_FILES = ("rotest.yaml", "rotest.yml",
                              ".rotest.yaml", ".rotest.yml")


class Option(object):
    """Configuration option, which can be derived from various sources.

    Attributes:
        command_line_options (iterable): CLI options, for example '--option'
            of '-O'.
        environment_variables (iterable): environment variables that have been
            set using `export` or `set` (depending on the platform).
        config_file_options (iterable): members in a YAML configuration file.
        default_value (str): a default value, to be used if no other input
            was given.
    """
    def __init__(self, command_line_options=(),
                 environment_variables=(), config_file_options=(),
                 default_value=None):
        self.command_line_options = command_line_options
        self.environment_variables = environment_variables
        self.config_file_options = config_file_options
        self.default_value = default_value


def get_command_line_configuration(configuration_schema, command_line_options):
    """Get configuration, based on the given arguments to the program.

    Notes:
        * The first argument is omitted, as it's the script path.
        * Both '--option=value' and '--option value' formats are supported.
        * Both '--<option>' and '-<option>' formats are supported.

    Args:
        configuration_schema (dict): a match between each target option to its
            sources.
        command_line_options (iterable): the program arguments, as given by
            `sys.argv`.

    Returns:
        dict: a match between each target option to the given value.
    """
    # Omitting the first argument, which is the script path
    command_line_options = command_line_options[1:]

    # Replacing every form of '--option=value' to '--option value'
    command_line_options = " ".join(command_line_options)
    command_line_options = command_line_options.replace("=", " ")
    command_line_options = command_line_options.split(" ")

    configuration = {}
    for command_line_option, value in zip(command_line_options[::2],
                                          command_line_options[1::2]):
        if (not command_line_option.startswith("--") and
                not command_line_option.startswith("-")):
            pass

        for target, option in six.iteritems(configuration_schema):
            if command_line_option in option.command_line_options:
                configuration[target] = value

    return configuration


def get_environment_variables_configuration(configuration_schema,
                                            environment_variables):
    """Get configuration, based on the environment variables.

    Args:
        configuration_schema (dict): a match between each target option to its
            sources.
        environment_variables (dict): the environment variables, as given by
            `os.environ`.

    Returns:
        dict: a match between each target option to the given value.
    """
    configuration = {}
    for target, option in six.iteritems(configuration_schema):
        for environment_variable in option.environment_variables:
            if environment_variable in environment_variables:
                configuration[target] = \
                    environment_variables[environment_variable]
                break

    return configuration


def search_config_file():
    """Search for configuration files in all ancestors of the current directory.

    Note:
        The permitted formats are: '.rotest.yml', 'rotest.yml',
        'rotest.yaml' and '.rotest.yaml'.

    Returns:
        str: path to the configuration file if found, None otherwise.
    """
    current_directory = os.path.abspath(".")

    while current_directory != os.path.dirname(current_directory):
        for filename in ROTEST_CONFIGURATION_FILES:
            config_candidate = os.path.join(current_directory, filename)
            if os.path.isfile(config_candidate):
                return config_candidate

        current_directory = os.path.dirname(current_directory)

    return None


def get_file_configuration(configuration_schema, config_content):
    """Get configuration, based on the configuration file.

    Args:
        configuration_schema (dict): a match between each target option to its
            sources.
        config_content (str): content of the configuration file in YAML format.

    Returns:
        dict: a match between each target option to the given value.
    """
    yaml_configuration = yaml.safe_load(config_content)
    if "rotest" not in yaml_configuration:
        return {}

    yaml_configuration = yaml_configuration["rotest"]

    configuration = {}
    for target, option in six.iteritems(configuration_schema):
        for config_file_option in option.config_file_options:
            if config_file_option in yaml_configuration:
                configuration[target] = yaml_configuration[config_file_option]
                break

    return configuration


def get_configuration(configuration_schema,
                      command_line_options=None,
                      environment_variables=None,
                      config_content=None):
    """Get configuration from all sources.

    Notes:
        * The priority is as follows: command line options first, then
          environment variables, than configuration from the configuration
          file, and at last the default values.

    Args:
        configuration_schema (dict): a match between each target option to its
            sources.
        command_line_options (iterable): the program arguments, as given by
            `sys.argv`.
        environment_variables (dict): the environment variables, as given by
            `os.environ`.
        config_content (str): content of the configuration file in YAML format.
    """
    default_configuration = {
        target: option.default_value
        for target, option in six.iteritems(configuration_schema)}

    if command_line_options is None:
        cli_configuration = {}
    else:
        cli_configuration = get_command_line_configuration(
            configuration_schema=configuration_schema,
            command_line_options=command_line_options)

    if environment_variables is None:
        env_var_configuration = {}
    else:
        env_var_configuration = get_environment_variables_configuration(
            configuration_schema=configuration_schema,
            environment_variables=environment_variables)

    if config_content is None:
        file_configuration = {}
    else:
        file_configuration = get_file_configuration(
            configuration_schema=configuration_schema,
            config_content=config_content)

    return AttrDict(dict(itertools.chain(
        iteritems(default_configuration),
        iteritems(file_configuration),
        iteritems(env_var_configuration),
        iteritems(cli_configuration),
    )))


CONFIGURATION_SCHEMA = {
    "workdir": Option(
        command_line_options=["--workdir"],
        environment_variables=["ROTEST_WORK_DIR"],
        config_file_options=["workdir"],
        default_value=os.path.expanduser("~/.rotest/")),
    "host": Option(
        command_line_options=["--host"],
        environment_variables=["ROTEST_HOST",
                               "RESOURCE_MANAGER_HOST"],
        config_file_options=["host"],
        default_value="localhost"),
    "port": Option(
        environment_variables=["ROTEST_SERVER_PORT"],
        config_file_options=["port"],
        default_value="8000"),
    "api_base_url": Option(
        command_line_options=["--api_base_url"],
        environment_variables=["ROTEST_API_BASE_URL"],
        config_file_options=["api_base_url"],
        default_value="rotest/api/"),
    "discoverer_blacklist": Option(
        config_file_options=["discoverer_blacklist"],
        default_value=[]),
    "shell_startup_commands": Option(
        config_file_options=["shell_startup_commands"],
        default_value=[]),
    "resource_request_timeout": Option(
        command_line_options=["--resource-request-timeout"],
        environment_variables=["ROTEST_RESOURCE_REQUEST_TIMEOUT",
                               "RESOURCE_WAITING_TIME"],
        config_file_options=["resource_request_timeout"],
        default_value=0),
    "django_settings": Option(
        command_line_options=["--django-settings"],
        environment_variables=["DJANGO_SETTINGS_MODULE",
                               "ROTEST_DJANGO_SETTINGS_MODULE"],
        config_file_options=["django_settings"],
        default_value=None),
    "artifacts_dir": Option(
        command_line_options=["--artifacts-dir"],
        environment_variables=["ARTIFACTS_DIR"],
        config_file_options=["artifacts_dir"],
        default_value=os.path.expanduser("~/.rotest/artifacts")),
}

config_path = search_config_file()
if config_path is None:
    configuration_content = None
else:
    with open(config_path, "r") as config_file:
        configuration_content = config_file.read()

CONFIGURATION = get_configuration(
    configuration_schema=CONFIGURATION_SCHEMA,
    command_line_options=sys.argv,
    environment_variables=os.environ,
    config_content=configuration_content)


DEFAULT_DISCOVERY_BLACKLIST = [".tox", ".git", ".idea", "setup.py"]


ROTEST_WORK_DIR = os.path.expanduser(CONFIGURATION.workdir)
RESOURCE_MANAGER_HOST = CONFIGURATION.host
DJANGO_MANAGER_PORT = int(CONFIGURATION.port)
API_BASE_URL = CONFIGURATION.api_base_url
RESOURCE_REQUEST_TIMEOUT = int(CONFIGURATION.resource_request_timeout)
DJANGO_SETTINGS_MODULE = CONFIGURATION.django_settings
ARTIFACTS_DIR = os.path.expanduser(CONFIGURATION.artifacts_dir)
SHELL_STARTUP_COMMANDS = CONFIGURATION.shell_startup_commands
DISCOVERER_BLACKLIST = list(CONFIGURATION.discoverer_blacklist) + \
                       DEFAULT_DISCOVERY_BLACKLIST

if DJANGO_SETTINGS_MODULE is None:
    raise ValueError("No Django settings module was supplied")

# Inject Django's settings module
os.environ["DJANGO_SETTINGS_MODULE"] = DJANGO_SETTINGS_MODULE

if os.path.isfile(ROTEST_WORK_DIR):
    raise ValueError("Path {} for the working directory is a file, you should "
                     "supply a directory".format(ROTEST_WORK_DIR))

if not os.path.isdir(ROTEST_WORK_DIR):
    os.mkdir(ROTEST_WORK_DIR)
