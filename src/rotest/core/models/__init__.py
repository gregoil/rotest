"""Define Rotest's core models.

The Django infrastructure expects a models.py file containing all the models
definitions for each application. This folder is a workaround used in order
to separate the different core application models into different files
"""
# pylint: disable=unused-import
from .run_data import RunData
from .case_data import CaseData
from .suite_data import SuiteData
from .signature import SignatureData
from .general_data import GeneralData
