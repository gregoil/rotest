"""Common Django configuration constants.

Settings/configuration for this Django project.

For more information about settings.py go to - settings.py documentation:
https://docs.djangoproject.com/en/dev/topics/settings/
"""
import os

# DB Configurations
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
                         'NAME': 'rotest',
                         'USER': '',
                         'PASSWORD': '',
                         'HOST': '',
                         'PORT': '',
                         'TEST_NAME': 'rotest_test'
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

TEST_RUNNER = 'test_runners.DjangoColorTestSuiteRunner'

ROOT_URLCONF = 'urls'

# URL prefix for static files.
STATIC_URL = '/static/'

SITE_ID = 1

SECRET_KEY = "rotest_secret_key"
