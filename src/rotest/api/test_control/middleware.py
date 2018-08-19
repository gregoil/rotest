# pylint: disable=unused-argument, no-self-use
SESSIONS = {}


def session_middleware(get_response):
    def middleware(request, *args, **kwargs):
        return get_response(request, sessions=SESSIONS, *args, **kwargs)

    return middleware


class SessionData(object):
    def __init__(self, all_tests, run_data, main_test, user_name):
        self.all_tests = all_tests
        self.run_data = run_data
        self.main_test = main_test
        self.user_name = user_name