"""Define core, test and resource loggers.

core_logger inherits from the system logger,
test logger inherits from core_logger
and resource_logger inherits from test_logger.
"""
# pylint: disable=too-many-arguments
import os
import logging
from logging.handlers import RotatingFileHandler

from termcolor import colored

from rotest.common.config import ROTEST_WORK_DIR
from rotest.common.constants import WHITE, BOLD, CYAN, YELLOW, RED, MAGENTA


LOG_FORMAT = ('<%(asctime)s>[%(levelname)s]' +
              '[%(module)s@%(lineno)d]: %(message)s')

# Core logger properties
CORE_LOG_BACKUP_COUNT = 20
CORE_LOG_NAME = 'core_logger'
CORE_LOG_MAX_BYTES = 1024 * 1024 * 20  # 20M
CORE_LOG_DIR = os.path.join(ROTEST_WORK_DIR, CORE_LOG_NAME)


class ColoredFormatter(logging.Formatter):
    """Define a colored log formatter.

    The formatter, in addition to formating the log record according to the
    given format, will add escape characters that define shell colors according
    to the log levels.
    """
    LEVEL_TO_COLOR = {logging.CRITICAL: (MAGENTA, [BOLD]),
                      logging.ERROR: (RED, [BOLD]),
                      logging.WARNING: (YELLOW, []),
                      logging.INFO: (WHITE, []),
                      logging.DEBUG: (CYAN, []),
                      logging.NOTSET: (WHITE, [])}

    def format(self, record):
        """Format the specified record.

        Args:
            record (LogRecord): instance representing the event being logged.

        Returns:
            str. the formatted log record (with color)
        """
        log_txt = super(ColoredFormatter, self).format(record)
        color, attrs = self.LEVEL_TO_COLOR[record.levelno]
        return colored(log_txt, color, attrs=attrs)


class LoggerWrapper(logging.Logger):
    """Picklable logger class.

    Since when running multiprocess on windows all objects are pickled (to be
    copied to the subprocess), and loggers aren't picklable, this wrapper is
    needed so that workers can recreate the various loggers when they run.
    """
    LOG_NAME_ATTR = "log_name"

    def __setstate__(self, state_dict):
        logger = logging.getLogger(state_dict[self.LOG_NAME_ATTR])
        self.__dict__.update(logger.__dict__)

    def __getstate__(self):
        return {self.LOG_NAME_ATTR: self.name}


logging.setLoggerClass(LoggerWrapper)


def define_logger(log_name, log_dir, log_level=logging.DEBUG,
                  log_format=LOG_FORMAT, rotating=True,
                  max_bytes=0, backup_count=0, is_colored=True):
    """Define logger.

    Args:
        log_name (str): logger name
        log_dir (str): logger output directory
        log_filename (str): logger output filename
        log_level (str): logger level
        log_format (str): logger format
        rotating (bool): if True - use RotatingFileHnadler as log_stream
                            else - use FileHandler as log_stream
        max_bytes (int): max length for log file
        backup_count (int) : number of old log files to save
        is_colored (bool): define colored logger or not.

    Returns:
        logging.Logger. logger
    """
    colored_to_formatters = {True: ColoredFormatter, False: logging.Formatter}

    logger = logging.getLogger(log_name)
    logger.setLevel(log_level)
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    file_path = os.path.join(log_dir, '%s.log' % log_name)
    if rotating:
        current_log_stream = RotatingFileHandler(filename=file_path,
                                                 maxBytes=max_bytes,
                                                 backupCount=backup_count)
    else:
        current_log_stream = logging.FileHandler(file_path)

    current_log_stream.setLevel(log_level)
    formatter = colored_to_formatters[is_colored](log_format)
    current_log_stream.setFormatter(formatter)
    logger.addHandler(current_log_stream)

    return logger


def define_core_logger(is_colored):
    """Define core_logger and add it to the system_logger handlers.

    This log will be written to core_logger directory in ROTEST_WORK_DIR,
    and will contain all necessary action of the infrastructure.

    Args:
        is_colored (bool): define colored core_logger or not.

    Returns:
        logging.Logger. core logger
    """
    logger = define_logger(CORE_LOG_NAME, CORE_LOG_DIR, rotating=True,
                           max_bytes=CORE_LOG_MAX_BYTES,
                           backup_count=CORE_LOG_BACKUP_COUNT,
                           is_colored=is_colored)

    logger.propagate = False

    return logger


def get_tree_path(test):
    """Get the identifiers tree path to the test.

    The hierarchical identifiers path is used to create inheritance between
    the loggers of the tests.

    Args:
        test (object): test instance to get the path for.
    """
    path = str(test.identifier)
    if test.parent is not None:
        return "%s.%s" % (get_tree_path(test.parent), path)

    return path


def get_test_logger(logger_basename, log_dir):
    """Define test_logger using define_logger method.

    This log will be written to work_dir, and will contain all necessary
    information about current test.

    Args:
        logger_basename (str): This is the logger name
        log_dir (str): This is the directory path

    Returns:
        logging.Logger. test logger
    """
    log_name = '%s.%s' % (CORE_LOG_NAME, logger_basename)

    logger = define_logger(log_name, log_dir, rotating=True,
                           max_bytes=CORE_LOG_MAX_BYTES,
                           backup_count=CORE_LOG_BACKUP_COUNT)

    return logger
