"""Test Rotest's Excel handler."""
# pylint: disable=protected-access
import os
import xlrd
import filecmp

from rotest.core.block import TestBlock
from base_result_handler_test import BaseResultHandlerTest
from rotest.common.colored_test_runner import colored_main
from rotest.core.result.handlers.excel_handler import ExcelHandler


class TestExcelHandler(BaseResultHandlerTest):
    """Test excel handler's functionality.

    Attributes:
        HEADERS_ROW (number): the row of the excel file headers.
        TESTS_COLUMN (number): the column of the tests tree.
        RESULT_COLUMN (number): the column of the test results.
        RESOURCES_COLUMN (number): the column of the test's resources.
        TRACEBACK_COLUMN (number): the column of the test's traceback.
        SUMMARY_RESULT_COLUMN (number): the column of the excel file summary.
        EXPECTED_FILE_PATH (str): the path to the expected result file.
        workbook (xlrd.book.Book): the workbook of the result file.
        worksheet (xlrd.sheet.Sheet): the worksheet of the result file.
        current_row (number): the current tested row.
    """
    HEADERS_ROW = 0
    TESTS_COLUMN = 0
    RESULT_COLUMN = 1
    TRACEBACK_COLUMN = 4
    RESOURCES_COLUMN = 6
    SUMMARY_RESULT_COLUMN = 0

    EXPECTED_FILE_PATH = os.path.join(os.path.dirname(__file__),
                                      'resources', 'expected_excel_output.xls')

    def setUp(self):
        """Define Excel workbook and worksheet."""
        super(TestExcelHandler, self).setUp()

        self.workbook = None
        self.worksheet = None
        self.current_row = None

    def get_result_handler(self):
        """Get an instance of ExcelHandler.

        Returns:
            TestExcelHandler. An instance of TestExcelHandler to test with.
        """
        return ExcelHandler(self.main_test)

    def _read_excel(self):
        """Read the excel workbook and sheet."""
        self.workbook = xlrd.open_workbook(self.handler.output_file_path)
        self.worksheet = self.workbook.sheet_by_index(0)

    def validate_headers(self):
        """Test that ExcelHandler writes the headers correctly.

        Raises:
            AsserationError. the headers were not written correctly.
        """
        for index, header in enumerate(ExcelHandler.HEADERS):
            actual_header = self.worksheet.cell_value(rowx=self.HEADERS_ROW,
                                                      colx=index)
            self.assertEqual(header, actual_header,
                             "The header of column %d should be %r. Got %r"
                             % (index + 1, header, actual_header))

    def validate_test_row(self, row, level, test_name):
        """Validate the test row in the tree.

        Args:
            row (number): test row.
            level (number): depth in the containing tests tree.
            test_name (str): test name as presented in the tree.

        Raises:
            AsserationError. the test row wasn't written correctly.
        """
        actual_test_row = self.worksheet.cell_value(rowx=row,
                                                    colx=self.TESTS_COLUMN)
        expected_test_row = level * ExcelHandler.SPACES + test_name
        self.assertEqual(expected_test_row, actual_test_row,
                         "In row %d expected %r. Got %r" %
                         ((row), expected_test_row, actual_test_row))

    def validate_tests_indentation(self, test, level=0):
        """Validate the given test indentation.

        Args:
            test (TestSuite / TestCase): test instance.
            level (number): depth in the containing tests tree.

        Raises:
            AsserationError. test tree doesn't include all the expected cases,
                in the right indentation.
        """
        self.current_row += 1
        if test.IS_COMPLEX is False:
            test_name = test.data.name
            self.validate_test_row(self.current_row, level, test_name)

        else:
            test_name = test.get_name()
            self.validate_test_row(self.current_row, level, test_name)

            for sub_test in test:
                self.validate_tests_indentation(sub_test, level + 1)

    def validate_hierarchy(self):
        """Test ExcelHandler's ability to write the hierarchy of the tests.

        Raises:
            AsserationError. the hierarchy in the Excel file didn't match the
                hierarchy of the test.
        """
        self.current_row = 0
        self.validate_tests_indentation(self.main_test)

    def validate_summary(self):
        """Test ExcelHandler writes result summary at the end of the file.

        Raises:
            AsserationError. test summary isn't as expected.
        """
        start_row = self.current_row + ExcelHandler.ROWS_TO_SKIP
        result_options = (ExcelHandler.IN_PROGRESS,
                          ExcelHandler.DID_NOT_RUN,
                          ExcelHandler.SUCCESS,
                          ExcelHandler.PASSED,
                          ExcelHandler.FAILED,
                          ExcelHandler.ERROR,
                          ExcelHandler.SKIPPED,
                          ExcelHandler.SKIPPED_SUMMARY_PATTERN % \
                                    ExcelHandler.TAGS_SKIP_MESSAGE,
                          ExcelHandler.EXPECTED_FAILURE,
                          ExcelHandler.UNEXPECTED_SUCCESS)

        for result_index, result in enumerate(result_options):
            current_row_index = start_row + result_index
            actual_result = self.worksheet.cell_value(rowx=current_row_index,
                                               colx=self.SUMMARY_RESULT_COLUMN)
            self.assertEqual(result, actual_result,
                             "On row %d column %d expected %r. Got %r" %
                             (current_row_index + 1, self.RESULT_COLUMN + 1,
                              result, actual_result))

    def validate_start_test_run(self):
        """Test ExcelHandler start_test_run method.

        * Validates file headers are written in the correct order.
        * Validates the test hierarchy and indentation.
        * Validates the test results summary.

        Raises:
            AsserationError. the test's Excel file was not created as expected.
        """
        self._read_excel()

        self.validate_headers()
        self.validate_hierarchy()
        self.validate_summary()

    def validate_result(self, test, result, traceback=""):
        """Validate adding result works.

        Args:
            test (Rotest.TestCase): the test its result was added.
            result (str): the result (e.g. "Success").
            traceback (str): the traceback of the test.

        Raises:
            AsserationError. the result isn't as expected.
        """
        if isinstance(test, TestBlock) is True:
            result = ExcelHandler.BLOCK_PREFIX + result

        self._read_excel()
        test_row = self.handler.test_to_row[test.identifier]
        displayed_row = test_row + 1

        actual_result = self.worksheet.cell_value(rowx=test_row,
                                                  colx=self.RESULT_COLUMN)
        self.assertEqual(result, actual_result,
                         "In row %d column %d expected: %r, got: %r" %
                         (displayed_row, 2, result, actual_result))

        resources = ''
        if test.locked_resources is not None:
            resources = '\n'.join("%s:%s" % (request_name, resource.name)
                                  for (request_name, resource) in
                                  test.locked_resources.iteritems())
        actual_resources = self.worksheet.cell_value(rowx=test_row,
                                                    colx=self.RESOURCES_COLUMN)
        self.assertEqual(resources, actual_resources,
                         "In row %d column %d expected: %r, got: %r" %
                         (displayed_row, self.RESOURCES_COLUMN, resources,
                          actual_resources))

        actual_traceback = self.worksheet.cell_value(rowx=test_row,
                                                    colx=self.TRACEBACK_COLUMN)
        self.assertEqual(traceback, actual_traceback,
                         "In row %d column %d expected: %r, got: %r" %
                         (displayed_row, self.TRACEBACK_COLUMN, traceback,
                          actual_traceback))

    def validate_stop_test_run(self):
        """Make a binary comparison.

        Raises:
            AsserationError. the result file differs from the expected file.
        """
        self.assertTrue(filecmp.cmp(self.EXPECTED_FILE_PATH,
                                    self.handler.output_file_path),
                        "The file %r differs from %r" %
                        (self.handler.output_file_path,
                         self.EXPECTED_FILE_PATH))


if __name__ == '__main__':
    colored_main(defaultTest='TestExcelHandler')
