"""Test Rotest's Logs behavior."""
from __future__ import absolute_import
import os
import time
import unittest

from rotest.common import core_log
from rotest.common.log import get_test_logger
from rotest.common.config import ROTEST_WORK_DIR


class TestLog(unittest.TestCase):
    """Test logs functionality."""

    TEST_LOG_BASENAME = 'logger_unittest'
    TEST_LOG_DIR = ROTEST_WORK_DIR

    @classmethod
    def setUpClass(cls):
        cls.core_log_file_path = cls._get_log_file_path(core_log)
        cls.test_log = get_test_logger(cls.TEST_LOG_BASENAME, cls.TEST_LOG_DIR)
        cls.test_log_file_path = cls._get_log_file_path(cls.test_log)

    @classmethod
    def tearDownClass(cls):
        for log_handler in cls.test_log.handlers:
            log_handler.close()

        os.remove(cls.test_log_file_path)

    @staticmethod
    def _get_log_file_path(logger):
        """Return the logger file handler file path."""
        for handler in logger.handlers:
            if hasattr(handler, 'baseFilename'):
                return handler.baseFilename

    def test_core_logger(self):
        """Log in core logger and verify logging occurs in this logger only."""
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
        """Log in test logger and verify logging occurs in both loggers."""
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
