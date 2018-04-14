"""Rotest testing framework, based on Python unit-test and Django."""
# pylint: disable=unused-import
from unittest import skip, SkipTest
from unittest import skipIf as skip_if

import colorama

from rotest.common import config


# Enable color printing on screen.
colorama.init()
