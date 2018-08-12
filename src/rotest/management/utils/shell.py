"""Rotest shell module, which enables using resources and running blocks."""
# pylint: disable=protected-access
import sys

import django
import IPython
from attrdict import AttrDict
from rotest.common.config import SHELL_APPS
from rotest.core.result.result import Result
from rotest.management.base_resource import BaseResource
from rotest.management.client.manager import ClientResourceManager
from rotest.core.runner import parse_config_file, DEFAULT_CONFIG_PATH
from rotest.management.utils.resources_discoverer import get_all_resources
from rotest.core.result.handlers.stream.log_handler import LogDebugHandler


# Mock tests result object for running blocks
blocks_result = Result(stream=None, descriptions=None,
                       outputs=[], main_test=None)


# Mock tests configuration for running blocks
blocks_config = AttrDict(parse_config_file(DEFAULT_CONFIG_PATH))


# Container for data shared between blocks
shared_data = {}


ENABLE_DEBUG = False


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


def run_block(block_class, **kwargs):
    """Run a block of the given class, passing extra parameters as arguments.

    Args:
        block_class (type): class inheriting from AbstractFlowComponent.
        kwargs (dict): additional arguments that will be passed as parameters
            to the block (overriding shared data).
    """
    shared_kwargs = shared_data.copy()
    shared_kwargs.update(kwargs)
    parent = ShellMockFlow()
    block_class = block_class.params(**shared_kwargs)

    block = block_class(config=blocks_config,
                        parent=parent,
                        enable_debug=ENABLE_DEBUG,
                        resource_manager=BaseResource._SHELL_CLIENT,
                        is_main=False)

    parent.work_dir = block.work_dir
    block.validate_inputs()
    block.run(blocks_result)


def main():
    django.setup()
    print "Creating client"
    BaseResource._SHELL_CLIENT = ClientResourceManager()
    BaseResource._SHELL_CLIENT.connect()
    LogDebugHandler(None, sys.stdout, None)  # Activate log to screen
    header = """Done! You can now lock resources and run tests, e.g.
    resource1 = ResourceClass.lock(skip_init=True, name='resource_name')
    resource2 = ResourceClass.lock(name='resource_name', config='config.json')
    shared_data['resource'] = resource1
    run_block(ResourceBlock, parameter=5)
    run_block(ResourceBlock.params(parameter=6), resource=resource2)
    """
    try:
        for app_name in SHELL_APPS:
            print "Loading resources from app", app_name
            resources = get_all_resources(app_name)
            globals().update(resources)

        IPython.embed(header=header,
                      module=sys.modules["__main__"],
                      user_ns=globals())

    finally:
        print "Releasing locked resources..."
        BaseResource._SHELL_CLIENT.disconnect()


if __name__ == "__main__":
    main()
