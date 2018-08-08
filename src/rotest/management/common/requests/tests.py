from rotest.management.common.requests.base_api import AbstractRequest


class ShouldSkip(AbstractRequest):
    URI = "tests/should_skip"
    METHOD = "GET"


class StartComposite(AbstractRequest):
    URI = "tests/start_composite"
    METHOD = "POST"


class StopComposite(AbstractRequest):
    URI = "tests/stop_composite"
    METHOD = "POST"


class StartTest(AbstractRequest):
    URI = "tests/start_test"
    METHOD = "POST"


class StopTest(AbstractRequest):
    URI = "tests/stop_test"
    METHOD = "POST"


class UpdateRunData(AbstractRequest):
    URI = "tests/update_run_data"
    METHOD = "POST"


class StartTestRun(AbstractRequest):
    URI = "tests/start_test_run"
    METHOD = "POST"


class AddTestResult(AbstractRequest):
    URI = "tests/add_test_result"
    METHOD = "POST"
