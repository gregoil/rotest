"""Django configuration file for developement."""
# pylint: disable=wildcard-import,unused-wildcard-import
from settings_common import *


INSTALLED_APPS = ('rotest.core',
                  'rotest.management',
                  'tests',
                  'playground',

                  # Administrator Related Applications
                  'django.contrib.auth',
                  'django.contrib.contenttypes',
                  'django.contrib.sessions',
                  'django.contrib.sites',
                  'django.contrib.messages',
                  'django.contrib.staticfiles',
                  'django.contrib.admin')
