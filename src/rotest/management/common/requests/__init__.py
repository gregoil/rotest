from .tests import *
from .fields import *
from .resources import *

REQUESTS = [
    AddTestResult,
    ShouldSkip,
    StartComposite,
    StartTest,
    StartTestRun,
    StopComposite,
    StopTest,
    UpdateRunData,
    LockResources,
    ReleaseResources,
    CleanupUser,
    QueryResources,
    UpdateFields
    ]
