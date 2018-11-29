"""Contain middleware and session handling of test control views."""
# pylint: disable=unused-argument,no-self-use
from future.builtins import object

SESSIONS = {}


def session_middleware(get_response):
    """Inject sessions to all test control views.

    Args:
        get_response (func): the response view to add the middleware to.
    """
    def middleware(request, *args, **kwargs):
        return get_response(request, sessions=SESSIONS, *args, **kwargs)

    return middleware


class SessionData(object):
    """Store session data.

    Attributes:
        all_tests (dict): stores all tests datas where key is `id` of the test
            and value is the actual test data.
        run_data (RunData): run data object that describes the test run.
        main_test (GeneralData): the main test of the run suite.
        resources (list): resources locked in the session.
    """
    def __init__(self):
        self.all_tests = None
        self.run_data = None
        self.main_test = None
        self.session_timeout = None
        self.resources = []
