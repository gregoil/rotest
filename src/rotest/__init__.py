"""Rotest testing framework, based on Python unit-test and Django."""
# pylint: disable=unused-import
import os
from unittest import skip, SkipTest
from unittest import skipIf as skip_if

import colorama

# Enable color printing on screen.
colorama.init()

DEFAULT_RESOURCE_WAITING_TIME = 0
WORK_DIR_ENVIROMENT_VAR = 'ROTEST_WORK_DIR'
ARTIFACT_DIR_ENVIROMENT_VAR = 'ARTIFACTS_DIR'
RESOURCE_WAITING_TIME = 'RESOURCE_WAITING_TIME'
RESOURCES_MANAGER_HOST_ENV_VAR = 'RESOURCE_MANAGER_HOST'
UT_SETTINGS_MODULE = 'rotest.common.django_utils.ut_settings'
DJANGO_SETTINGS_MODULE = 'rotest.common.django_utils.all_settings'

if WORK_DIR_ENVIROMENT_VAR not in os.environ:
    raise RuntimeError("Environment variable %r was not set properly" %
                       WORK_DIR_ENVIROMENT_VAR)

ROTEST_WORK_DIR = os.environ[WORK_DIR_ENVIROMENT_VAR]

if not os.path.exists(ROTEST_WORK_DIR):
    raise RuntimeError("'%s' [%s] is not a valid work directory"
                       % (WORK_DIR_ENVIROMENT_VAR, ROTEST_WORK_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)

os.environ.setdefault(RESOURCE_WAITING_TIME,
                      str(DEFAULT_RESOURCE_WAITING_TIME))
RESOURCE_REQUEST_TIMEOUT = int(os.environ[RESOURCE_WAITING_TIME])
