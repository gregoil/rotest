"""Rotest testing framework, based on Python unit-test and Django."""
# pylint: disable=unused-import, wrong-import-position
from __future__ import absolute_import

import os
from unittest import skip, SkipTest, skipIf as skip_if

DEFAULT_SETTINGS_PATH = "rotest.common.django_utils.settings"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", DEFAULT_SETTINGS_PATH)

import django
import colorama

if not hasattr(django, 'apps'):  # noqa
    django.setup()

from .common import config

# Enable color printing on screen.
colorama.init()
