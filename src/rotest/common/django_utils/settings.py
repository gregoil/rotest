"""Django configuration file for developement."""
# pylint: disable=wildcard-import,unused-wildcard-import
from __future__ import absolute_import
import os


INSTALLED_APPS = (
    'rotest.core',
    'rotest.management',

    # Administrator Related Applications
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin'
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'rotest_db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'TEST_NAME': 'test_rotest_db',
    },

}

# Defining middleware classes
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware')


# Set the time zone
TIME_ZONE = 'America/Chicago'

# Fixtures are .json files representation of the DB used for UT
FIXTURE_DIRS = [os.path.join(os.path.dirname(__file__), 'fixtures')]

# Debug flag - used to expose internal site errors
DEBUG = True

ROOT_URLCONF = 'rotest.common.django_utils.urls'

# URL prefix for static files.
STATIC_URL = '/static/'

SITE_ID = 1

SECRET_KEY = "rotest_secret_key"
