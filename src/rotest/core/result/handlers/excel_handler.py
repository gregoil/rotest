"""Excel result handler."""
# pylint: disable=unused-argument
from __future__ import absolute_import

import os
from collections import OrderedDict

import six
import xlwt
from xlwt.Style import easyxf
from future.builtins import str
from future.utils import iteritems

from rotest.core.suite import TestSuite
from rotest.core.flow_component import AbstractFlowComponent
from rotest.core.result.handlers.db_handler import DBHandler
from rotest.core.models.case_data import CaseData, TestOutcome
from rotest.core.result.handlers.remote_db_handler import RemoteDBHandler
from rotest.core.result.handlers.abstract_handler import AbstractResultHandler


class ExcelHandler(AbstractResultHandler):
    """Excel result handler.

    Overrides result handler's methods to generate an Excel result file.

    Attributes:
        row_number (num): current Excel sheet row number to write to.
        test_to_row (dict): match between test name to the row number to
            which it was written.
        verbosity (num): whether to include traceback in the Excel report.
        output_file_path (str): the Excel report path.
        workbook (xlwt.Workbook): Excel workbook object.
        sheet (xlwt.Sheet): Excel sheet object.
    """
    NAME = 'excel'

    SPACES = "    "
    EXCEL_FILE_ENCODING = "utf-8"
    EXCEL_SHEET_NAME = "TestResults"
    EXCEL_WORKBOOK_NAME = "results.xls"

    RESULT_CHOICES = CaseData.RESULT_CHOICES

    BLOCK_PREFIX = "Block "
    IN_PROGRESS = "In Progress"
    DID_NOT_RUN = "Did Not Run"
    PASSED = "Previously Passed"
    ERROR = RESULT_CHOICES[TestOutcome.ERROR]
    FAILED = RESULT_CHOICES[TestOutcome.FAILED]
    SUCCESS = RESULT_CHOICES[TestOutcome.SUCCESS]
    SKIPPED = RESULT_CHOICES[TestOutcome.SKIPPED]
    EXPECTED_FAILURE = RESULT_CHOICES[TestOutcome.EXPECTED_FAILURE]
    UNEXPECTED_SUCCESS = RESULT_CHOICES[TestOutcome.UNEXPECTED_SUCCESS]

    BLACK_COLOR = "black"
    WHITE_COLOR = "white"

    FAILED_COLOR = "red"
    PASSED_COLOR = "lime"
    ERROR_COLOR = "dark_red"
    SKIPPED_COLOR = "yellow"
    IN_PROGRESS_COLOR = "brown"
    DEFAULT_COLOR = WHITE_COLOR
    DID_NOT_RUN_COLOR = "grey25"
    SUCCESS_COLOR = "bright_green"
    EXPECTED_FAILURE_COLOR = "turquoise"
    UNEXPECTED_SUCCESS_COLOR = "turquoise"

    RESULT = 'Result'
    NAME_HEADER = 'Name'
    ASSIGNEE = 'Assignee'
    COMMENTS = 'Comments'
    END_TIME = 'End time'
    RESOURCES = 'Resources'
    TRACEBACK = 'Traceback'
    START_TIME = 'Start time'
    DESCRIPTION = 'Description'
    HEADERS = (NAME_HEADER, RESULT, START_TIME, END_TIME, TRACEBACK,
               DESCRIPTION, RESOURCES, ASSIGNEE, COMMENTS)

    CHAR_LENGTH = 256  # Character length is in units of 1/256
    MAX_TRACEBACK_LENGTH = 32767  # Max length of Excel cell content
    HEADER_TO_WIDTH = {RESULT: CHAR_LENGTH * 22,
                       ASSIGNEE: CHAR_LENGTH * 13,
                       COMMENTS: CHAR_LENGTH * 82,
                       END_TIME: CHAR_LENGTH * 26,
                       RESOURCES: CHAR_LENGTH * 48,
                       TRACEBACK: CHAR_LENGTH * 82,
                       START_TIME: CHAR_LENGTH * 26,
                       DESCRIPTION: CHAR_LENGTH * 82,
                       NAME_HEADER: CHAR_LENGTH * 75}

    ROW_HEIGHT = 20 * 13  # 13pt
    FONT_COLOR = "font:colour %s;"
    HEIGHT_STYLE = 'font:height %s, bold on;' % ROW_HEIGHT
    COLOR_PATTERN = 'pattern: pattern solid, fore_colour %s;'
    THIN_CELL_BORDERS = ('borders: left thin, right thin, '
                         'top thin, bottom thin;')
    THICK_CELL_BORDERS = ('borders: left thick, right thick, '
                          'top thick, bottom thick;')
    CELL_STYLE = COLOR_PATTERN + THIN_CELL_BORDERS + FONT_COLOR

    DEFAULT_CELL_STYLE = easyxf(CELL_STYLE % (DEFAULT_COLOR, BLACK_COLOR))
    BOLDED_CELL_STYLE = easyxf(THICK_CELL_BORDERS + HEIGHT_STYLE)
    CONTENT_TO_STYLE = OrderedDict([
        (IN_PROGRESS, easyxf(CELL_STYLE % (IN_PROGRESS_COLOR, WHITE_COLOR))),
        (DID_NOT_RUN, easyxf(CELL_STYLE % (DID_NOT_RUN_COLOR, BLACK_COLOR))),
        (SUCCESS, easyxf(CELL_STYLE % (SUCCESS_COLOR, BLACK_COLOR))),
        (PASSED, easyxf(CELL_STYLE % (PASSED_COLOR, BLACK_COLOR))),
        (FAILED, easyxf(CELL_STYLE % (FAILED_COLOR, WHITE_COLOR))),
        (ERROR, easyxf(CELL_STYLE % (ERROR_COLOR, WHITE_COLOR))),
        (SKIPPED, easyxf(CELL_STYLE % (SKIPPED_COLOR, BLACK_COLOR))),
        (EXPECTED_FAILURE, easyxf(CELL_STYLE % (EXPECTED_FAILURE_COLOR,
                                               BLACK_COLOR))),
        (UNEXPECTED_SUCCESS, easyxf(CELL_STYLE % (UNEXPECTED_SUCCESS_COLOR,
                                                 BLACK_COLOR)))])

    LOCAL_DB_SKIP_MESSAGE = DBHandler.SKIP_DELTA_MESSAGE
    REMOTE_DB_SKIP_MESSAGE = RemoteDBHandler.SKIP_DELTA_MESSAGE
    PASSED_MESSAGES = (LOCAL_DB_SKIP_MESSAGE, REMOTE_DB_SKIP_MESSAGE)

    SKIPPED_SUMMARY_PATTERN = "    Skipped: %s"

    ROWS_TO_SKIP = 3

    SUMMARY_RESULT_TYPE_COLUMN = HEADERS[0]
    SUMMARY_RESULT_COUNTER_COLUMN = HEADERS[1]

    RESULT_COLUMN = "B"
    TRACEBACK_COLUMN = "E"
    FORMULA_PATTERN = 'COUNTIF(%s1:%s%d,"%s")'

    MAX_SUMMERIZE_SIZE = len(CONTENT_TO_STYLE) + ROWS_TO_SKIP + 1

    def __init__(self, main_test, output_file_path=None, *args, **kwargs):
        """Initialize Excel workbook and Sheet.

        Args:
            main_test (object): the main test instance (e.g. TestSuite instance
                or TestFlow instance).
            output_file_path (str): path to create the excel file in. Leave
                None to create at the test's working dir with the default name.
        """
        super(ExcelHandler, self).__init__(main_test)

        self.row_number = 0
        self.test_to_row = {}
        self.output_file_path = output_file_path
        if self.output_file_path is None:
            self.output_file_path = os.path.join(self.main_test.work_dir,
                                                 self.EXCEL_WORKBOOK_NAME)

        self.workbook = xlwt.Workbook(encoding=self.EXCEL_FILE_ENCODING)
        self.sheet = self.workbook.add_sheet(self.EXCEL_SHEET_NAME,
                                             cell_overwrite_ok=True)

    def start_test(self, test):
        """Update the Excel that a test case starts.

        Args:
            test (object): test item instance.
        """
        self._write_test_result(test)

        self.workbook.save(self.output_file_path)

    def stop_test(self, test):
        """Called when the given test has been run.

        Args:
            test (object): test item instance.
        """
        self._write_test_result(test)

        self.workbook.save(self.output_file_path)

    def start_test_run(self):
        """Generate initial Excel report according to the root test.

        Creates a primary report containing all sub test of the root test.
        All tests will start with "Did Not Run" status.
        """
        self._write_headers()
        self._generate_initial_excel(self.main_test)
        self._create_result_summary()
        self._align_columns()

        self.workbook.save(self.output_file_path)

        self.row_number += 1

    def update_resources(self, test):
        """Write the test's resources to the Excel file.

        Args:
            test (object): test item instance.
        """
        # write resources
        if test.locked_resources is not None:
            resources = '\n'.join("%s:%s" % (request_name, resource.name)
                                  for (request_name, resource) in
                                  iteritems(test.locked_resources))
        else:
            resources = ''

        self._write_to_cell(self.test_to_row[test.identifier], self.RESOURCES,
                            self.DEFAULT_CELL_STYLE, resources)

    def add_success(self, test, msg):
        """Update the test Excel entry's result to success.

        Args:
            test (object): test item instance.
            msg (str): success message.
        """
        self._write_test_result(test)
        self.workbook.save(self.output_file_path)

    def add_skip(self, test, reason):
        """Update the test Excel entry's result to skip.

        Args:
            test (object): test item instance.
            reason (str): skip reason description.
        """
        self._write_test_result(test)
        self.workbook.save(self.output_file_path)

    def add_failure(self, test, exception_str):
        """Update the test Excel entry's result to failure.

        Args:
            test (object): test item instance.
            exception_str (str): exception traceback string.
        """
        self._write_test_result(test)
        self.workbook.save(self.output_file_path)

    def add_error(self, test, exception_str):
        """Update the test Excel entry's result to error.

        Args:
            test (object): test item instance.
            exception_str (str): exception traceback string.
        """
        self._write_test_result(test)
        self.workbook.save(self.output_file_path)

    def add_expected_failure(self, test, exception_str):
        """Update the test Excel entry's result to expected failure.

        Args:
            test (object): test item instance.
            exception_str (str): exception traceback string.
        """
        self._write_test_result(test)
        self.workbook.save(self.output_file_path)

    def add_unexpected_success(self, test):
        """Update the test Excel entry's result to unexpected success.

        Args:
            test (object): test item instance.
        """
        self._write_test_result(test)
        self.workbook.save(self.output_file_path)

    def _generate_initial_excel(self, test):
        """Create an initial Excel test result.

        Generate test entries by the root test's

        Args:
            test (object): test item instance.
        """
        self.row_number += 1

        self._write_to_cell(self.row_number, self.NAME_HEADER,
                            self.DEFAULT_CELL_STYLE,
                            (test.parents_count * self.SPACES) +
                             test.data.name)

        self._write_to_cell(self.row_number, self.DESCRIPTION,
                            self.DEFAULT_CELL_STYLE,
                            test.__doc__)

        status = self.DID_NOT_RUN
        status_desc = status
        if isinstance(test, AbstractFlowComponent) and not test.is_main:
            status_desc = self.BLOCK_PREFIX + status

        if not isinstance(test, TestSuite):
            self._write_to_cell(self.row_number, self.RESULT,
                                self.CONTENT_TO_STYLE[status],
                                status_desc)

            self.test_to_row[test.identifier] = self.row_number

        if test.IS_COMPLEX:
            for sub_test in test:
                self._generate_initial_excel(sub_test)

    def _write_test_result(self, test):
        """Write a single test entry to the Excel file.

        Args:
            test (object): test item instance.
        """
        # write result status
        row_num = self.test_to_row[test.identifier]
        if test.data.exception_type is None:
            status = self.IN_PROGRESS

        else:
            status = self.RESULT_CHOICES[test.data.exception_type]

        status_desc = status
        tb_str = test.data.traceback

        if status == self.SKIPPED and tb_str in self.PASSED_MESSAGES:
            status = status_desc = self.PASSED

        if isinstance(test, AbstractFlowComponent) and not test.is_main:
            status_desc = self.BLOCK_PREFIX + status

        if test.data.start_time is not None:
            self._write_to_cell(row_num, self.START_TIME,
                                self.DEFAULT_CELL_STYLE,
                                str(test.data.start_time))

        if test.data.end_time is not None:
            self._write_to_cell(row_num, self.END_TIME,
                                self.DEFAULT_CELL_STYLE,
                                str(test.data.end_time))

        self._write_to_cell(row_num, self.RESULT,
                            self.CONTENT_TO_STYLE[status], status_desc)

        if tb_str is not None and len(tb_str) > self.MAX_TRACEBACK_LENGTH:
            tb_str = tb_str[-1 * self.MAX_TRACEBACK_LENGTH:]

        self._write_to_cell(row_num, self.TRACEBACK,
                            self.DEFAULT_CELL_STYLE, tb_str)

        # set row's height
        self.sheet.row(row_num).height_mismatch = True
        self.sheet.row(row_num).height = self.ROW_HEIGHT

    def _write_to_cell(self, row_number, header, style, content):
        """Write content to a specific cell.

        Args:
            row_number (number): cell's row number.
            header (str): header of the cell's column.
            style (xlwt.Style): representation of an Excel format.
            content (str): content to be written to the cell.
        """
        self.sheet.row(row_number).write(self.HEADERS.index(header),
                                         content, style)

    def _write_headers(self):
        """Write the column headers."""
        for header in self.HEADERS:
            self._write_to_cell(self.row_number, header,
                                self.BOLDED_CELL_STYLE, header)

    def _align_columns(self):
        """Align the columns width."""
        for header, col_width in six.iteritems(self.HEADER_TO_WIDTH):
            self.sheet.col(self.HEADERS.index(header)).width = col_width

    def _create_result_summary(self):
        """Create result summary at the end of the Excel report."""
        self.row_number += self.ROWS_TO_SKIP

        for result_type in self.CONTENT_TO_STYLE:
            self._write_to_cell(self.row_number,
                                self.SUMMARY_RESULT_TYPE_COLUMN,
                                self.CONTENT_TO_STYLE[result_type],
                                result_type)

            result_type_count = xlwt.Formula(self.FORMULA_PATTERN %
                                             (self.RESULT_COLUMN,
                                              self.RESULT_COLUMN,
                                              self.row_number,
                                              result_type))
            self._write_to_cell(self.row_number,
                                self.SUMMARY_RESULT_COUNTER_COLUMN,
                                self.DEFAULT_CELL_STYLE,
                                result_type_count)

            self.row_number += 1
