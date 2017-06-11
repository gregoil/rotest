"""Define all Rotest Tests.

The Django infrastructure expects a tests.py file containing all the unit tests
for each application. This folder is a workaround used in order to separate the
different tests into different files
"""
# pylint: disable=unused-import,relative-import
from core.test_case import TestTestCase
from core.test_flow import TestTestFlow
from core.test_suite import TestTestSuite
from core.test_run_delta import TestRunDelta
from management.test_parser import TestXMLParser
from core.test_filter_tests import TestTagsMatching
from management.test_result_manager import TestResultManagement
from core.handlers_tests.test_xml_handler import TestXMLHandler
from management.test_resource_manager import TestResourceManagement
from core.multiprocess.test_timeout import TestMultiprocessTimeouts
from core.handlers_tests.test_excel_handler import TestExcelHandler
from core.handlers_tests.test_signature_handler import TestSignatureHandler
from core.test_runner_results import (TestBaseRunnerResult,
                                      TestMultiprocessRunnerResult)
from core.multiprocess.test_runner import (TestMultiprocessRunner,
                                           TestMultipleWorkers)
from management.test_parallel import (TwoClientsParallelCase,
                                      MultipleClientsParallelCase)
