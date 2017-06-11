"""Django configuration file for developement."""
# pylint: disable=wildcard-import,unused-wildcard-import
from settings_common import *


INSTALLED_APPS = ('rotest.core',
                  'rotest.management',
                  'tests',

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
