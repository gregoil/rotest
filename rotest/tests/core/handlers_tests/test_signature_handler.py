"""Test Rotest's Signatures handler."""
# pylint: disable=protected-access
import os
import xlrd

from base_result_handler_test import BaseResultHandlerTest
from rotest.common.colored_test_runner import colored_main
from rotest.core.result.handlers.signature_handler import SignatureHandler


class TestSignatureHandler(BaseResultHandlerTest):
    """Test issues signatures handler's functionality."""
    fixtures = ['signature_ut.json']

    SIG_DICT = {"Error": "test_res2",
                "Failed": "test_res1"}

    def setUp(self):
        super(TestSignatureHandler, self).setUp()

        self.output_file_path = os.path.join(self.main_test.work_dir,
                                        SignatureHandler.EXCEL_WORKBOOK_NAME)

        self.lines_read = ['Test']
        self.current_row = 0

    def load_worksheet(self):
        """Update the worksheet the test is using."""
        self.workbook = xlrd.open_workbook(self.handler.output_file_path)
        self.worksheet = self.workbook.sheet_by_index(0)

    def get_result_handler(self):
        """Get an instance of SignatureHandler.

        Returns:
            SignatureHandler. An instance of SignatureHandler to test with.
        """
        return SignatureHandler(self.main_test)

    def validate_start_test_run(self):
        """Validate the output of the handler's start_test_run method."""
        self.load_worksheet()

        for index, header in enumerate(SignatureHandler.HEADERS):
            actual_header = self.worksheet.cell_value(rowx=self.current_row,
                                                      colx=index)
            self.assertEqual(header, actual_header,
                             "The header of column %d should be %r. Got %r"
                             % (index + 1, header, actual_header))

        self.current_row += 1

    def get_new_signature(self):
        """Get the new signature detected at the report file.

        Yields:
            str. lines added to the report file.
        """
        self.load_worksheet()

        try:
            test_name = self.worksheet.cell_value(rowx=self.current_row,
                                                  colx=0)
            if test_name not in self.lines_read:
                self.lines_read.append(test_name)
                sig_name = self.worksheet.cell_value(rowx=self.current_row,
                                                     colx=1)
                self.current_row += 1
                return sig_name

        except IndexError:
            pass

    def validate_result(self, test, result, traceback=""):
        """Validate adding result works.

        Args:
            test (rotest.core.case.TestCase): the test its result was added.
            result (str): the result (e.g. "Success").
            traceback (str): the traceback of the test.

        Raises:
            AssertionError. the result isn't as expected.
        """
        if result in self.SIG_DICT:
            expected_name = self.SIG_DICT[result]
            sig_name = self.get_new_signature()

            self.assertEqual(sig_name, expected_name,
                             "Signature name written %r does not match "
                             "expected %r" % (sig_name, expected_name))
        else:
            self.assertRaises(IndexError, self.worksheet.cell_value,
                              rowx=self.current_row, colx=0)


if __name__ == '__main__':
    colored_main(defaultTest='TestSignatureHandler')
