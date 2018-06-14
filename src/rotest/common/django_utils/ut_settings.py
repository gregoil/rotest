# pylint: disable=wildcard-import,unused-wildcard-import
import platform

from rotest.common import core_log
from rotest.common.django_utils.settings import *


if platform.system() == 'Windows':  # pragma: no cover
    try:
        import win32file

        core_log.debug("Setting 2048 as the file descriptors limit")
        win32file._setmaxstdio(2048)  # pylint: disable=protected-access
    except ImportError:
        import warnings
        warnings.warn("Cannot find package 'win32file'. "
                      "You must install it using 'pip install pypiwin32'")
