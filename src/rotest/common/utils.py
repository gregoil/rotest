"""Common useful utils."""
# pylint: disable=protected-access
import os
from shutil import copy
from itertools import count
from datetime import datetime


RUNTIME_ORDER = '-start_time'
DATE_TIME_FORMAT = '%y.%m.%d_%H_%M_%S'


def safe_copy(src_file, dst_file):
    """Copy src_file to temp file and then rename it to dst_file.

    Args:
        src_file (str): src file path
        dst_file (str): dst file path
    """
    temp_dst_file = '%s.temp' % dst_file
    copy(src_file, temp_dst_file)
    os.rename(temp_dst_file, dst_file)


def get_test_index(test):
    """Get the index of the test under its parent or None if it's the top.

    The returned index starts count at 1.

    Returns:
        number. test's index under its parent.
    """
    if test.parent is None:
        return None

    return test.parent._tests.index(test) + 1


def get_work_dir(base_dir, test_name, test_item):
    """Get the working directory for the given test.

    Creates a work directory for by joining the given base directory,
    the test name and the current date time string. If the work directory
    already exists the new one will get the copy number extension.

    Args:
        base_dir (str): base directory path.
        test_name (str): test name.
        test_item (object): test instance.

    Returns:
        str. path of the working directory.
    """
    if test_item is None:
        basic_work_dir = test_name

    else:
        test_index = get_test_index(test_item)
        if test_index is None:
            basic_work_dir = datetime.strftime(datetime.now(),
                                               DATE_TIME_FORMAT)

        else:
            basic_work_dir = "%d_%s" % (test_index, test_name)

    basic_work_dir = os.path.join(base_dir, basic_work_dir)
    work_dir = basic_work_dir

    copy_count = count()
    while os.path.exists(work_dir):
        work_dir = basic_work_dir + '(%s)' % copy_count.next()

    os.makedirs(work_dir)
    return work_dir
