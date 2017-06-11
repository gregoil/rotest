"""Django configuration for server side"""
# pylint: disable=wildcard-import,unused-wildcard-import
from settings_common import *


INSTALLED_APPS = ('rotest.management',

                  # Administrator Related Applications
                  'django.contrib.auth',
                  'django.contrib.contenttypes',
                  'django.contrib.sessions',
                  'django.contrib.sites',
                  'django.contrib.messages',
                  'django.contrib.staticfiles',
                  'django.contrib.admin')
