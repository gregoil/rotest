"""Rotest testing framework, based on Python unit-test and Django."""
# pylint: disable=unused-import
from unittest import skip, SkipTest, skipIf as skip_if

import colorama

from rotest.common import config
from rotest.cli.client import main


# Enable color printing on screen.
colorama.init()
