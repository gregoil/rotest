"""Django configuration file for developement."""
# pylint: disable=wildcard-import,unused-wildcard-import,protected-access
import os
import platform

from rotest.common import core_log


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
        'NAME': 'rotest_ut',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'TEST_NAME': 'rotest_ut_test'
    }
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

ROOT_URLCONF = 'urls'

# URL prefix for static files.
STATIC_URL = '/static/'

SITE_ID = 1

SECRET_KEY = "rotest_secret_key"

if platform.system() == 'Windows':
    try:
        import win32file
    except ImportError:
        raise RuntimeError("Cannot find package 'win32file'. Install it using "
                           "'pip install pypiwin32'")

    core_log.debug("Setting 2048 as the file descriptors limit")
    win32file._setmaxstdio(2048)  # pylint: disable=protected-access
