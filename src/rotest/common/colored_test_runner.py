"""Define a unittest test runner and result for rotest's UT."""
# pylint: disable=protected-access,invalid-name
import unittest
from functools import partial

from termcolor import COLORS

from .constants import GREEN, RED, YELLOW


DEFAULT = 0


def template(text):
    return '\33[%dm' % text


class ColorTextTestResult(unittest._TextTestResult):
    """Unittest's text result object, with colored printing."""
    def addSuccess(self, test):
        self.stream.write(template(COLORS[GREEN]))
        super(ColorTextTestResult, self).addSuccess(test)
        self.stream.write(template(DEFAULT))

    def addError(self, test, err):
        self.stream.write(template(COLORS[RED]))
        super(ColorTextTestResult, self).addError(test, err)
        self.stream.write(template(DEFAULT))

    def addFailure(self, test, err):
        self.stream.write(template(COLORS[RED]))
        super(ColorTextTestResult, self).addFailure(test, err)
        self.stream.write(template(DEFAULT))

    def addSkip(self, test, reason):
        self.stream.write(template(COLORS[YELLOW]))
        super(ColorTextTestResult, self).addSkip(test, reason)
        self.stream.write(template(DEFAULT))


class ColorTextTestRunner(unittest.TextTestRunner):
    """Unittest's runner, that uses high verbosity and colored printing."""
    def __init__(self, *args, **kwargs):
        super(ColorTextTestRunner, self).__init__(*args, **kwargs)
        self.verbosity = 2  # Always verbose

    def _makeResult(self):
        return ColorTextTestResult(self.stream, self.descriptions,
                                   self.verbosity)


colored_main = partial(unittest.main, testRunner=ColorTextTestRunner)
