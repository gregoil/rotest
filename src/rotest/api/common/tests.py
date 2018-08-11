from swagapi.api.base_api import AbstractRequest

from rotest.api.test_control.middleware import SessionMiddleware
from rotest.api.test_control.views.add_test_result import add_test_result
from rotest.api.test_control.views.should_skip import should_skip
from rotest.api.test_control.views.start_composite import start_composite
from rotest.api.test_control.views.start_test import start_test
from rotest.api.test_control.views.start_test_run import start_test_run
from rotest.api.test_control.views.stop_composite import stop_composite
from rotest.api.test_control.views.stop_test import stop_test
from rotest.api.test_control.views.update_run_data import update_run_data


class ShouldSkip(AbstractRequest):
    """Check if the test passed in the last run according to results DB."""
    URI = "tests/should_skip"
    METHOD = "GET"
    TAGS = ["Tests"]
    PARAMS = [

    ]
    VIEW = SessionMiddleware(should_skip)


class StartComposite(AbstractRequest):
    """Update the test data to 'in progress' state and set the start time."""
    URI = "tests/start_composite"
    METHOD = "POST"
    TAGS = ["Tests"]
    PARAMS = [

    ]
    VIEW = SessionMiddleware(start_composite)


class StopComposite(AbstractRequest):
    """Save the composite test's data."""
    URI = "tests/stop_composite"
    METHOD = "POST"
    TAGS = ["Tests"]
    PARAMS = [

    ]
    VIEW = SessionMiddleware(stop_composite)


class StartTest(AbstractRequest):
    """Update the test data to 'in progress' state and set the start time."""
    URI = "tests/start_test"
    METHOD = "POST"
    TAGS = ["Tests"]
    PARAMS = [

    ]
    VIEW = SessionMiddleware(start_test)


class StopTest(AbstractRequest):
    """End a test run."""
    URI = "tests/stop_test"
    METHOD = "POST"
    TAGS = ["Tests"]
    PARAMS = [

    ]
    VIEW = SessionMiddleware(stop_test)


class UpdateRunData(AbstractRequest):
    """Update the tests run data."""
    URI = "tests/update_run_data"
    METHOD = "POST"
    TAGS = ["Tests"]
    PARAMS = [

    ]
    VIEW = SessionMiddleware(update_run_data)


class StartTestRun(AbstractRequest):
    """Initialize the tests run data."""
    URI = "tests/start_test_run"
    METHOD = "POST"
    TAGS = ["Tests"]
    PARAMS = [

    ]
    VIEW = SessionMiddleware(start_test_run)


class AddTestResult(AbstractRequest):
    """Add a result to the test."""
    URI = "tests/add_test_result"
    METHOD = "POST"
    TAGS = ["Tests"]
    PARAMS = [

    ]
    VIEW = SessionMiddleware(add_test_result)
