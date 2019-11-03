# pylint: disable=too-many-locals,redefined-outer-name
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
        import rotest
        rotest.core.TestCase = TestCase
        rotest.core.TestFlow = TestFlow
        rotest.core.create_flow = create_flow
        rotest.core.TestBlock = TestBlock
        rotest.core.TestSuite = TestSuite
        rotest.core.request = request
        rotest.core.MODE_CRITICAL = MODE_CRITICAL
        rotest.core.MODE_FINALLY = MODE_FINALLY
        rotest.core.MODE_OPTIONAL = MODE_OPTIONAL
        rotest.core.Pipe = Pipe
        rotest.core.BlockInput = BlockInput
        rotest.core.BlockOutput = BlockOutput
        rotest.core.AbstractMonitor = AbstractMonitor
        rotest.core.AbstractResourceMonitor = AbstractResourceMonitor
        rotest.core.require_attr = require_attr
        rotest.core.skip_if_case = skip_if_case
        rotest.core.skip_if_flow = skip_if_flow
        rotest.core.skip_if_block = skip_if_block
        rotest.core.skip_if_not_main = skip_if_not_main


default_app_config = "rotest.core.CoreConfig"
