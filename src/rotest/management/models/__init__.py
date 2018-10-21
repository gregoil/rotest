"""Define Rotest's common models.

The Django infrastructure expects a models.py file containing all the models
definitions for each application. This folder is a workaround used in order
to separate the different common application models into different files.
"""
# pylint: disable=unused-import
from __future__ import absolute_import
from rotest.management.models.resource_data import ResourceData
from rotest.management.models.ut_models import \
                                DemoResourceData, DemoComplexResourceData
