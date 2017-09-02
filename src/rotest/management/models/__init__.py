"""Define Rotest's common models.

The Django infrastructure expects a models.py file containing all the models
definitions for each application. This folder is a workaround used in order
to separate the different common application models into different files.
"""
# pylint: disable=unused-import
from resource_data import ResourceData
from ut_models import DemoResourceData, DemoComplexResourceData
