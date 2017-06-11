"""Test Rotest's XML handler."""
# pylint: disable=protected-access
import os

import xmltodict

from rotest.core.block import TestBlock
from base_result_handler_test import BaseResultHandlerTest
from rotest.common.colored_test_runner import colored_main
from rotest.core.result.handlers.xml_handler import XMLHandler


class TestXMLHandler(BaseResultHandlerTest):
    """Test XML handler's functionality."""
    XML_FILES_PATH = os.path.join(os.path.dirname(__file__),
                                  'resources', 'xml_files')
    EXPECTED_XML_FILES = [os.path.join(XML_FILES_PATH, 'flow_success.xml'),
                          os.path.join(XML_FILES_PATH, 'flow_fail.xml'),
                          os.path.join(XML_FILES_PATH, 'success.xml'),
                          os.path.join(XML_FILES_PATH, 'error.xml'),
                          os.path.join(XML_FILES_PATH, 'fail.xml'),
                          os.path.join(XML_FILES_PATH, 'skip.xml'),
                          os.path.join(XML_FILES_PATH,
                                       'expected_failure.xml'),
                          os.path.join(XML_FILES_PATH,
                                       'unexpected_success.xml')]

    def setUp(self):
        """Create expected XML files iterator"""
        super(TestXMLHandler, self).setUp()
        self.expected_xml_files = iter(self.EXPECTED_XML_FILES)

    def get_result_handler(self):
        """Get an instance of XMLHandler.

        Returns:
            XMLHandler. An instance of XMLHandler to test with.
        """
        return XMLHandler(self.main_test)

    def validate_result(self, test, result, traceback=""):
        """Validate adding result gives the expected output.

        Args:
            test (rotest.core.case.TestCase): the test its result was added.
            result (str): result to add to the test.
            traceback (str): the traceback of the test.

        Raises:
            AssertionError. the result wasn't added as expected.
        """
        if isinstance(test, TestBlock):
            return

        result_xml_file = os.path.join(test.work_dir,
                                       XMLHandler.XML_REPORT_PATH)

        expected_xml_file = self.expected_xml_files.next()

        expected_xml = xmltodict.parse(open(expected_xml_file, "rt").read(),
                                       dict_constructor=dict)
        result_xml = xmltodict.parse(open(result_xml_file, "rt").read(),
                                     dict_constructor=dict)

        self.assertEqual(expected_xml, result_xml)


if __name__ == '__main__':
    colored_main(defaultTest='TestXMLHandler')
