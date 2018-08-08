from rotest.management.common.requests.base_api import AbstractRequest


class ShouldSkip(AbstractRequest):
    """Check if the test passed in the last run according to results DB"""
    URI = "tests/should_skip"
    METHOD = "GET"
    TAGS = ["Tests"]
    PARAMS = [

    ]


class StartComposite(AbstractRequest):
    """Update the test data to 'in progress' state and set the start time"""
    URI = "tests/start_composite"
    METHOD = "POST"
    TAGS = ["Tests"]
    PARAMS = [

    ]


class StopComposite(AbstractRequest):
    """Save the composite test's data"""
    URI = "tests/stop_composite"
    METHOD = "POST"
    TAGS = ["Tests"]
    PARAMS = [

    ]


class StartTest(AbstractRequest):
    """"Update the test data to 'in progress' state and set the start time"""
    URI = "tests/start_test"
    METHOD = "POST"
    TAGS = ["Tests"]
    PARAMS = [

    ]


class StopTest(AbstractRequest):
    """"End a test run"""
    URI = "tests/stop_test"
    METHOD = "POST"
    TAGS = ["Tests"]
    PARAMS = [

    ]


class UpdateRunData(AbstractRequest):
    """Update the tests run data"""
    URI = "tests/update_run_data"
    METHOD = "POST"
    TAGS = ["Tests"]
    PARAMS = [

    ]


class StartTestRun(AbstractRequest):
    """Initialize the tests run data"""
    URI = "tests/start_test_run"
    METHOD = "POST"
    TAGS = ["Tests"]
    PARAMS = [

    ]


class AddTestResult(AbstractRequest):
    """Add a result to the test"""
    URI = "tests/add_test_result"
    METHOD = "POST"
    TAGS = ["Tests"]
    PARAMS = [

    ]
