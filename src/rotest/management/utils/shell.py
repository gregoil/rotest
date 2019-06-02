"""Rotest shell module, which enables using resources and running blocks."""
# pylint: disable=protected-access
from __future__ import print_function, absolute_import

import sys

import django
import IPython
from attrdict import AttrDict
from future.builtins import object
from rotest.core.suite import TestSuite
from rotest.core.result.result import Result
from rotest.common.config import SHELL_STARTUP_COMMANDS
from rotest.management.base_resource import BaseResource
from rotest.core.flow_component import AbstractFlowComponent
from rotest.management.client.manager import ClientResourceManager
from rotest.core.runner import parse_config_file, DEFAULT_CONFIG_PATH
from rotest.core.result.handlers.stream.log_handler import LogDebugHandler


# Mock tests result object for running blocks
result_object = Result(stream=None, descriptions=None,
                       outputs=[], main_test=None)


# Mock tests configuration for running blocks
default_config = AttrDict(parse_config_file(DEFAULT_CONFIG_PATH))


# Container for data shared between blocks
shared_data = {}


ENABLE_DEBUG = False
IMPORT_BLOCK_UTILS = \
    "from rotest.management.utils.shell import shared_data, run_test"
IMPORT_RESOURCE_LOADER = \
    "from rotest.management.utils.resources_discoverer import get_resources"


class ShellMockFlow(object):
    """Mock class used for sharing data between blocks."""
    parents_count = 0

    def __init__(self):
        self._tests = []
        self.parent = None
        self.identifier = 0
        self.work_dir = None

    def _set_parameters(self, override_previous=True, **kwargs):
        shared_data.update(kwargs)
        for test_item in self._tests:
            test_item._set_parameters(override_previous, **kwargs)

    def __iter__(self):
        return iter([])

    def addTest(self, test):
        self._tests.append(test)

    def request_resources(self, resources_to_request, *args, **kwargs):
        for test_item in self._tests:
            test_item.request_resources(resources_to_request, *args, **kwargs)
            request_names = [request.name for request in resources_to_request]
            test_item.share_data(**{name: getattr(test_item, name)
                                    for name in request_names})


def _run_block(block_class, debug=ENABLE_DEBUG, **kwargs):
    """Run a block of the given class, passing extra parameters as arguments.

    Args:
        block_class (type): class inheriting from AbstractFlowComponent.
        debug (bool): whether to run the test in debug mode or not.
        kwargs (dict): additional arguments that will be passed as parameters
            to the block (overriding shared data).
    """
    shared_kwargs = block_class.common.copy()
    shared_kwargs.update(shared_data)
    shared_kwargs.update(kwargs)
    parent = ShellMockFlow()
    block_class = block_class.params(**shared_kwargs)

    block = block_class(config=default_config,
                        parent=parent,
                        enable_debug=debug,
                        resource_manager=BaseResource._SHELL_CLIENT,
                        is_main=False)

    parent.work_dir = block.work_dir
    block.validate_inputs()
    block.run(result_object)


def run_test(test_class, debug=ENABLE_DEBUG, **kwargs):
    """Run a test of the given class, passing extra parameters as arguments.

    Args:
        test_class (type): class inheriting from AbstractTest.
        debug (bool): whether to run the test in debug mode or not.
        kwargs (dict): additional arguments that will be passed as parameters
            if the test is a block or flow (overriding shared data).
    """
    if issubclass(test_class, AbstractFlowComponent):
        return _run_block(test_class, debug=debug, **kwargs)

    if not test_class.IS_COMPLEX:
        class AlmightySuite(TestSuite):
            components = [test_class]

        test_class = AlmightySuite

    test = test_class(config=default_config,
                      enable_debug=debug,
                      resource_manager=BaseResource._SHELL_CLIENT)

    test.run(result_object)


def main():
    django.setup()

    print("Creating client")
    BaseResource._SHELL_CLIENT = ClientResourceManager()
    LogDebugHandler(None, sys.stdout, None)  # Activate log to screen

    print("""Done! You can now lock resources and run tests, e.g.
    resource1 = ResourceClass.lock(skip_init=True, name='resource_name')
    resource2 = ResourceClass.lock(name='resource_name', config='config.json')
    shared_data['resource'] = resource1
    run_test(ResourceBlock, parameter=5)
    run_test(ResourceBlock.params(parameter=6), resource=resource2)
    run_test(SomeTestCase, debug=True)
    """)

    startup_commands = [IMPORT_BLOCK_UTILS, IMPORT_RESOURCE_LOADER]
    startup_commands.append("imported_resources = get_resources();"
                            "print('Importing resources:'); "
                            "print(', '.join(imported_resources.keys()));"
                            "globals().update(imported_resources)")
    startup_commands.extend(SHELL_STARTUP_COMMANDS)
    try:
        IPython.start_ipython(["-i", "--no-banner",
                               "-c", ";".join(startup_commands)])

    finally:
        print("Releasing locked resources...")
        BaseResource._SHELL_CLIENT.disconnect()


if __name__ == "__main__":
    main()
