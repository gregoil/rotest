"""Rotest testing framework, based on Python unit-test and Django."""
# pylint: disable=unused-import
from __future__ import absolute_import
from unittest import skip, SkipTest, skipIf as skip_if

import django
import colorama

from .common import config
if not hasattr(django, 'apps'):  # noqa
    django.setup()


# Enable color printing on screen.
colorama.init()
