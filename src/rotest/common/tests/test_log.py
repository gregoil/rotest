"""Test Rotest's Logs behavior."""
import os
import time
import unittest

from rotest import ROTEST_WORK_DIR
from rotest.common import core_log
from rotest.common.log import get_test_logger
from rotest.common.colored_test_runner import colored_main


class TestLog(unittest.TestCase):
    """Test logs functionality."""

    TEST_LOG_BASENAME = 'logger_unittest'
    TEST_LOG_DIR = ROTEST_WORK_DIR

    @classmethod
    def setUpClass(cls):
        cls.core_log_file_path = cls._get_log_file_path(core_log)
        cls.test_log = get_test_logger(cls.TEST_LOG_BASENAME, cls.TEST_LOG_DIR)
        cls.test_log_file_path = cls._get_log_file_path(TestLog.test_log)

    @classmethod
    def tearDownClass(cls):
        os.remove(TestLog.test_log_file_path)

    @staticmethod
    def _get_log_file_path(logger):
        """Return the logger file handler file path."""
        for handler in logger.handlers:
            if hasattr(handler, 'baseFilename'):
                return handler.baseFilename

    def test_core_logger(self):
        """Add log print and verify only one occurrence in core log file
        """
        with open(self.core_log_file_path, 'r') as core_log_file:
            with open(self.test_log_file_path, 'r') as test_log_file:
                log_msg = '%s TEST_CORE_LOGGER' % time.ctime()
                core_log_file.seek(0, os.SEEK_END)
                test_log_file.seek(0, os.SEEK_END)
                core_log.debug(log_msg)
                core_log_file_content = core_log_file.read()
                test_log_file_content = test_log_file.read()
                self.assertEquals(core_log_file_content.count(log_msg), 1)
                self.assertEquals(test_log_file_content.count(log_msg), 0)

    def test_test_logger(self):
        """Add log print and verify only one occurrence in core & test log file
        """
        with open(self.core_log_file_path, 'r') as core_log_file:
            with open(self.test_log_file_path, 'r') as test_log_file:
                log_msg = '%s TEST_TEST_LOGGER' % time.ctime()
                core_log_file.seek(0, os.SEEK_END)
                test_log_file.seek(0, os.SEEK_END)
                self.test_log.debug(log_msg)
                core_log_file_content = core_log_file.read()
                test_log_file_content = test_log_file.read()
                self.assertEquals(core_log_file_content.count(log_msg), 1)
                self.assertEquals(test_log_file_content.count(log_msg), 1)


if __name__ == '__main__':
    colored_main(defaultTest='TestLog')
