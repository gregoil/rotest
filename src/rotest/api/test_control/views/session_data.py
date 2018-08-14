"""Session data class."""

# pylint: disable=unused-argument, no-self-use


class SessionData(object):
    def __init__(self, all_tests, run_data, main_test, user_name):
        self.all_tests = all_tests
        self.run_data = run_data
        self.main_test = main_test
        self.user_name = user_name
