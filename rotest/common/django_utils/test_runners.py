"""Define Django tests runners."""
from django.test.simple import DjangoTestSuiteRunner

from rotest.common.colored_test_runner import ColorTextTestRunner


class DjangoColorTestSuiteRunner(DjangoTestSuiteRunner):
    """Django test runner that uses ColorTextTestRunner."""
    def run_suite(self, suite, **kwargs):
        return ColorTextTestRunner(verbosity=self.verbosity,
                                   failfast=self.failfast).run(suite)
