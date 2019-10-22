"""Rotest testing framework, based on Python unit-test and Django."""
# pylint: disable=unused-import, wrong-import-position
from __future__ import absolute_import
from unittest import skip, SkipTest, skipIf as skip_if

import django
import colorama

if not hasattr(django, 'apps'):  # noqa
    django.setup()

from .common import config

# Enable color printing on screen.
colorama.init()
