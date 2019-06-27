from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "rotest.core"

    def ready(self):
        from .case import TestCase
        from .flow import TestFlow, create_flow
        from .block import TestBlock
        from .suite import TestSuite
        from .abstract_test import request
        from .flow_component import (MODE_CRITICAL, MODE_FINALLY, MODE_OPTIONAL,
                                     Pipe, BlockInput, BlockOutput)
        from .result.monitor.monitor import (AbstractMonitor,
                                             AbstractResourceMonitor,
                                             require_attr, skip_if_case,
                                             skip_if_flow,
                                             skip_if_block, skip_if_not_main)
        from rotest import core
        core.TestCase = TestCase
        core.TestFlow = TestFlow
        core.create_flow = create_flow
        core.TestBlock = TestBlock
        core.TestSuite = TestSuite
        core.request = request
        core.MODE_CRITICAL = MODE_CRITICAL
        core.MODE_FINALLY = MODE_FINALLY
        core.MODE_OPTIONAL = MODE_OPTIONAL
        core.Pipe = Pipe
        core.BlockInput = BlockInput
        core.BlockOutput = BlockOutput
        core.AbstractMonitor = AbstractMonitor
        core.AbstractResourceMonitor = AbstractResourceMonitor
        core.require_attr = require_attr
        core.skip_if_case = skip_if_case
        core.skip_if_flow = skip_if_flow
        core.skip_if_block = skip_if_block
        core.skip_if_not_main = skip_if_not_main


default_app_config = "rotest.core.CoreConfig"
