"""Known issues result handler."""
import re
import os

import xlwt
from xlwt.Style import easyxf

from rotest.core.models.signature import SignatureData
from rotest.core.result.handlers.abstract_handler import AbstractResultHandler


class SignatureHandler(AbstractResultHandler):
    """Failures signatures result handler.

    Matches the tests' exceptions with a given pattern,
    and reports it to the user.
    """
    NAME = 'signature'

    LINK = 'Link'
    TEST = 'Test'
    PATTERN = 'Pattern'
    ISSUE_NAME = 'Issue name'
    HEADERS = (TEST, ISSUE_NAME, LINK, PATTERN)

    BLACK_COLOR = "black"
    WHITE_COLOR = "white"
    DEFAULT_COLOR = WHITE_COLOR

    CHAR_LENGTH = 256  # Character length is in units of 1/256
    COL_WIDTH = CHAR_LENGTH * 30

    ROW_HEIGHT = 20 * 13  # 13pt
    FONT_COLOR = "font:colour %s;"
    HEIGHT_STYLE = 'font:height %s, bold on;' % ROW_HEIGHT
    COLOR_PATTERN = 'pattern: pattern solid, fore_colour %s;'
    THIN_CELL_BORDERS = ('borders: left thin, right thin, '
                         'top thin, bottom thin;')
    THICK_CELL_BORDERS = ('borders: left thick, right thick, '
                          'top thick, bottom thick;')
    CELL_STYLE = COLOR_PATTERN + THIN_CELL_BORDERS + FONT_COLOR
    BOLDED_CELL_STYLE = easyxf(THICK_CELL_BORDERS + HEIGHT_STYLE)
    DEFAULT_CELL_STYLE = easyxf(CELL_STYLE % (DEFAULT_COLOR, BLACK_COLOR))

    EXCEL_FILE_ENCODING = "utf-8"
    EXCEL_SHEET_NAME = "MatchingSignatures"
    EXCEL_WORKBOOK_NAME = "signatures.xls"

    def __init__(self, main_test=None, *args, **kwargs):
        """Initialize the result handler.

        Note:
            Loads the signatures from the DB.

        Args:
            main_test (object): the main test instance.
        """
        super(SignatureHandler, self).__init__(main_test, *args, **kwargs)

        self.row_number = 0
        self.signatures = SignatureData.objects.all()
        self.output_file_path = os.path.join(self.main_test.work_dir,
                                             self.EXCEL_WORKBOOK_NAME)

        self.workbook = xlwt.Workbook(encoding=self.EXCEL_FILE_ENCODING)
        self.sheet = self.workbook.add_sheet(self.EXCEL_SHEET_NAME,
                                             cell_overwrite_ok=True)
        self._prepare_excel_file()

    def _write_to_cell(self, header, style, content):
        """Write content to a specific cell.

        Args:
            header (str): header of the cell's column.
            style (xlwt.Style): representation of an Excel format.
            content (str): content to be written to the cell.
        """
        self.sheet.row(self.row_number).write(self.HEADERS.index(header),
                                              content, style)

    def _write_headers(self):
        """Write the column headers."""
        for header in self.HEADERS:
            self._write_to_cell(header, self.BOLDED_CELL_STYLE, header)

        self.row_number += 1

    def _align_columns(self):
        """Align the columns width."""
        for header in self.HEADERS:
            self.sheet.col(self.HEADERS.index(header)).width = self.COL_WIDTH

    def _prepare_excel_file(self):
        """Prepare the excel file before writing any data to it."""
        self._write_headers()
        self._align_columns()

        self.workbook.save(self.output_file_path)

    def _match_signatures(self, exception_str):
        """Return the name of the matched signature.

        Args:
            exception_str (str): exception traceback string.

        Returns:
            SignatureData. the signature of the given exception.
        """
        for signature in self.signatures:
            signature_reg = re.compile(signature.pattern,
                                       re.DOTALL | re.MULTILINE)
            if signature_reg.match(exception_str):
                return signature

    def _register_result_of_known_issues(self, test, exception_str):
        """Register the name of the matched signature.

        Args:
            test (object): test item instance.
            exception_str (str): exception traceback string.
        """
        signature_match = self._match_signatures(exception_str)
        if signature_match is not None:
            # Inserting test name
            self._write_to_cell(header=self.TEST,
                                content=test.data.name,
                                style=self.DEFAULT_CELL_STYLE)

            # Inserting signature/issue name
            self._write_to_cell(header=self.ISSUE_NAME,
                                content=signature_match.name,
                                style=self.DEFAULT_CELL_STYLE)

            # Inserting link
            self._write_to_cell(header=self.LINK,
                                content=signature_match.link,
                                style=self.DEFAULT_CELL_STYLE)

            # Inserting pattern
            self._write_to_cell(header=self.PATTERN,
                                content=signature_match.pattern,
                                style=self.DEFAULT_CELL_STYLE)

            self.row_number += 1

            self.workbook.save(self.output_file_path)

    def add_error(self, test, exception_str):
        """Check if the test error matches any known issues.

        Args:
            test (object): test item instance.
            exception_str (str): exception traceback string.
        """
        self._register_result_of_known_issues(test, exception_str)

    def add_failure(self, test, exception_str):
        """Check if the test failure matches any known issues.

        Args:
            test (object): test item instance.
            exception_str (str): exception traceback string.
        """
        self._register_result_of_known_issues(test, exception_str)
