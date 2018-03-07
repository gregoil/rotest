"""Django configuration file for developement."""
# pylint: disable=wildcard-import,unused-wildcard-import,protected-access
import platform

from rotest.common import core_log
from settings_common import *


INSTALLED_APPS = ('rotest.core',
                  'rotest.management',

                  # Administrator Related Applications
                  'django.contrib.auth',
                  'django.contrib.contenttypes',
                  'django.contrib.sessions',
                  'django.contrib.sites',
                  'django.contrib.messages',
                  'django.contrib.staticfiles',
                  'django.contrib.admin')


DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
                         'NAME': 'rotest_ut',
                         'USER': '',
                         'PASSWORD': '',
                         'HOST': '',
                         'PORT': '',
                         'TEST_NAME': 'rotest_ut_test'
                         }
             }

if platform.system() == 'Windows':
    try:
        core_log.debug("Setting 2048 as the file descriptors limit")
        import win32file
        win32file._setmaxstdio(2048)

    except ImportError:
        raise RuntimeError("Cannot find package 'win32file'. Install it using "
                           "'pip install pypiwin32'")
