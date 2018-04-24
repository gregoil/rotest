"""XML result handler."""
# pylint: disable=invalid-name,too-few-public-methods,arguments-differ
# pylint: disable=too-many-arguments
import os

from lxml import etree
from lxml.builder import E

from rotest.core.flow import TestFlow
from rotest.core.flow_component import AbstractFlowComponent
from rotest.core.result.handlers.abstract_handler import AbstractResultHandler


class XMLHandler(AbstractResultHandler):
    """JUnit XML handler.

    Overrides result handler's method to generate JUnit compatible XML reports
    per test.
    """
    NAME = "xml"

    XML_REPORT_PATH = "result.xml"

    def _create_xml_report(self, test, xml_obj):
        """Save an XML object to the report file in the test's work dir.

        Args:
            test (object): test item instance.
            xml_obj (lxml.builder.E): the xml content's description.
        """
        xml_report_path = os.path.join(test.work_dir,
                                       self.XML_REPORT_PATH)
        with open(xml_report_path, 'w') as xml_report:
            xml_report.write(etree.tostring(xml_obj, pretty_print=True))

    def _add_test_report(self, test, result_description="",
                         error=False, failure=False):
        """Generate an XML report for the given test in its work directory.

        Args:
            test (object): test item instance.
            result_description (lxml.builder.E / str): result description
                (e.g. E.result() / "result").
            error (bool): whether the test result is considered an Error.
            failure (bool): whether the test result is considered a Failure.
        """
        if isinstance(test, AbstractFlowComponent) and not test.is_main:
            return

        if isinstance(test, TestFlow):
            test_name = test.data.name
            method_name = TestFlow.TEST_METHOD_NAME

        else:
            test_name, method_name = test.data.name.split(".")

        test_case = E.testcase(result_description, {"classname": test_name,
                                                    "name": method_name})
        test_suite = E.testsuite(test_case, {"errors": str(int(error)),
                                             "failures": str(int(failure)),
                                             "name": test_name,
                                             "tests": "1"})

        self._create_xml_report(test, test_suite)

    def add_success(self, test):
        """Called when a test has completed successfully.

        Args:
            test (object): test item instance.
        """
        self._add_test_report(test)

    def add_skip(self, test, reason):
        """Called when a test is skipped.

        Args:
            test (object): test item instance.
            reason (str): skip reason description.
        """
        skipped = E.skipped(reason)
        self._add_test_report(test, result_description=skipped)

    def add_failure(self, test, exception_string):
        """Called when a failure has occurred.

        Args:
            test (object): test item instance.
            exception_str (str): exception traceback string.
        """
        failure = E.failure(exception_string)
        self._add_test_report(test, result_description=failure,
                              error=False, failure=True)

    def add_expected_failure(self, test, exception_string):
        """Called when an expected failure has occurred.

        The expected failure is considered as success.

        Args:
            test (object): test item instance.
            exception_str (str): exception traceback string.
        """
        self._add_test_report(test, result_description=exception_string)

    def add_error(self, test, exception_string):
        """Called when an error occurred.

        Args:
            test (object): test item instance.
            exception_str (str): exception traceback string.
        """
        error = E.error(exception_string)
        self._add_test_report(test, result_description=error,
                              error=True, failure=False)

    def add_unexpected_success(self, test):
        """Called when a test was expected to fail, but succeed.

        The unexpected success is considered as failure.

        Args:
            test (object): test item instance.
        """
        failure = E.failure("Unexpected Success")
        self._add_test_report(test, result_description=failure,
                              error=False, failure=True)
