"""Common useful utils."""
import os
from shutil import copy
from itertools import count
from datetime import datetime


RUNTIME_ORDER = '-start_time'
DATE_TIME_FORMAT = '_%y.%m.%d_%H_%M_%S'


class AttrDict(dict):
    """A dictionary that allows attribute-like access to its values.

    Example:

    >>> dct = AttrDict({'name': 'John', 'age': 29, 'child':
                              {'name': 'Wendy', 'age': 3}})
    >>> print dct.name, dct.age
    John 29
    >>> print dct.child.name
    Wendy
    >>> dct.name = 'Jane'
    >>> dct.eye_color = 'Blue'
    >>> print dct.items()
    [('eye_color', 'Blue'), ('age', 29), ('name', 'Jane')]
    """
    def __init__(self, *args):
        temp_dict = args

        if temp_dict != ():
            temp_dict, = temp_dict

            for key, value in temp_dict.items():
                if isinstance(value, dict):
                    temp_dict[key] = AttrDict(value)

        super(AttrDict, self).__init__(*(temp_dict,))

    def __getattr__(self, attr):
        if attr in self:
            return self[attr]

        raise AttributeError("AttrDict has no attribute %r" % attr)

    def __setattr__(self, attr, value):
        self[attr] = value

    def __dir__(self):
        return dir(dict) + self.keys()


def safe_copy(src_file, dst_file):
    """Copy src_file to temp file and then rename it to dst_file.

    Args:
        src_file (str): src file path
        dst_file (str): dst file path
    """
    temp_dst_file = '%s.temp' % dst_file
    copy(src_file, temp_dst_file)
    os.rename(temp_dst_file, dst_file)


def get_work_dir(base_dir, test_name):
    """Get the working directory for the given test.

    Creates a work directory for by joining the given base directory,
    the test name and the current date time string. If the work directory
    already exists the new one will get the copy number extension.

    Args:
        base_dir (str): base directory path.
        test_name (str): test name.

    Returns:
        str. path of the working directory.
    """
    date_postfix = datetime.strftime(datetime.now(), DATE_TIME_FORMAT)
    basic_work_dir = os.path.join(base_dir, test_name + date_postfix)
    work_dir = basic_work_dir

    copy_count = count()
    while os.path.exists(work_dir) is True:
        work_dir = basic_work_dir + '(%s)' % copy_count.next()

    os.makedirs(work_dir)
    return work_dir
