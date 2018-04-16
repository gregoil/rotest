# pylint: disable=wildcard-import,unused-wildcard-import
import platform

from rotest.common import core_log
from rotest.common.django_utils.settings import *


if platform.system() == 'Windows':
    try:
        import win32file
    except ImportError:
        raise RuntimeError("Cannot find package 'win32file'. Install it using "
                           "'pip install pypiwin32'")

    core_log.debug("Setting 2048 as the file descriptors limit")
    win32file._setmaxstdio(2048)  # pylint: disable=protected-access
