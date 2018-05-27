"""Utils module for pretty-printing the logs."""
import os
import sys
import math
import struct
from abc import ABCMeta, abstractproperty

import enum
from termcolor import colored

from rotest.core.case import TestCase
from rotest.core.flow import TestFlow
from rotest.core.suite import TestSuite
from rotest.core.block import TestBlock

STDERR_HANDLE_NUMBER = -12
CSBI_BUFFER_SIZE = 22


class TitleConfiguration(object):
    """Interface for specifying the colors that will be printed in a test.

    Attributes:
        result (TestResult): result of the test.
    """
    __metaclass__ = ABCMeta

    def __init__(self, result):
        self.result = result

    has_multi_line_decoration = False
    decoration_character = "-"

    @abstractproperty
    def decoration_color(self):
        """Define the color of the decoration.

        Returns:
            str. name of the color to color the decoration.
        """
        pass

    @abstractproperty
    def test_type_color(self):
        """Define the color of the test type.

        Returns:
            str. name of the color to color the test type("Block"/"Flow")
        """
        pass

    @abstractproperty
    def test_name_color(self):
        """Define the color of the test's name.

        Returns:
            str. name of the color to color the test name.
        """
        pass

    @abstractproperty
    def test_result_color(self):
        """Define the color of the test's result.

        Returns:
            str. name of the color to color the test name.
        """
        pass

    @staticmethod
    def from_test(test, result):
        """Return a configuration matching the test supplied.

        Returns:
            TestConfiguration. configuration that matches a given test.

        Raises:
            TypeError: If given any test that is not an AbstractTest.
        """
        if test.IS_COMPLEX:
            return ComplexTitleConfiguration(result)

        return NonComplexTitleConfiguration(result)


class NonComplexTitleConfiguration(TitleConfiguration):
    """Title configuration for tests that are not complex."""
    @property
    def decoration_color(self):
        colors = {
            TestResult.failure: "red",
            TestResult.error: "red",
            TestResult.skip: "white",
            TestResult.success: "green",
            TestResult.started: "white",
            TestResult.expected_failure: "green",
            TestResult.unexpected_success: "red",
        }

        return colors[self.result]

    @property
    def test_type_color(self):
        colors = {
            TestResult.failure: "red",
            TestResult.error: "red",
            TestResult.skip: "white",
            TestResult.success: "green",
            TestResult.started: "white",
            TestResult.expected_failure: "green",
            TestResult.unexpected_success: "red",
        }

        return colors[self.result]

    @property
    def test_result_color(self):
        colors = {
            TestResult.failure: "red",
            TestResult.error: "red",
            TestResult.skip: "white",
            TestResult.success: "green",
            TestResult.started: "white",
            TestResult.expected_failure: "green",
            TestResult.unexpected_success: "red",
        }

        return colors[self.result]

    @property
    def test_name_color(self):
        colors = {
            TestResult.failure: "red",
            TestResult.error: "red",
            TestResult.skip: "yellow",
            TestResult.success: "green",
            TestResult.started: "cyan",
            TestResult.expected_failure: "green",
            TestResult.unexpected_success: "red",
        }
        return colors[self.result]


class ComplexTitleConfiguration(TitleConfiguration):
    """Title configuration for complex tests."""
    has_multi_line_decoration = True
    decoration_character = "="

    @property
    def decoration_color(self):
        colors = {
            TestResult.failure: "red",
            TestResult.error: "red",
            TestResult.skip: "white",
            TestResult.success: "green",
            TestResult.started: "white",
            TestResult.expected_failure: "green",
            TestResult.unexpected_success: "red",
        }

        return colors[self.result]

    @property
    def test_result_color(self):
        colors = {
            TestResult.failure: "red",
            TestResult.error: "red",
            TestResult.skip: "white",
            TestResult.success: "green",
            TestResult.started: "white",
            TestResult.expected_failure: "green",
            TestResult.unexpected_success: "red",
        }

        return colors[self.result]

    @property
    def test_type_color(self):
        colors = {
            TestResult.failure: "red",
            TestResult.error: "red",
            TestResult.skip: "white",
            TestResult.success: "green",
            TestResult.started: "white",
            TestResult.expected_failure: "green",
            TestResult.unexpected_success: "red",
        }

        return colors[self.result]

    @property
    def test_name_color(self):
        colors = {
            TestResult.failure: "red",
            TestResult.error: "red",
            TestResult.skip: "yellow",
            TestResult.success: "green",
            TestResult.started: "blue",
            TestResult.expected_failure: "green",
            TestResult.unexpected_success: "red",
        }
        return colors[self.result]


class TestResult(enum.Enum):
    success = "success"
    skip = "skip"
    error = "error"
    failure = "fail"
    started = "started"
    expected_failure = "expected failure"
    unexpected_success = "unexpected success"

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return str(self) == other


class Pretty(object):
    """Title with decoration.

    Attributes:
        test (AbstractTest): encapsulated test to generate its title.
        result (TestResult): result that the tests ended with (or didn't end).
        configuration (TitleConfiguration): title's configuration of colors.
    """

    def __init__(self, test, result):
        self.test = test
        self.result = result
        self.configuration = TitleConfiguration.from_test(test, result)

    def __str__(self):
        line = ("{multi_line_decoration}"
                "{decoration_left}"
                " {test_type}: {test_name} ({result}) "
                "{decoration_right}"
                "{multi_line_decoration}")

        return line.format(
            multi_line_decoration=self.multi_line_decoration(),
            decoration_left=self.left_decoration(),
            test_type=self.test_type(),
            test_name=self.test_name(),
            result=self.test_result(),
            decoration_right=self.right_decoration()
        )

    def left_decoration(self):
        decoration_color = self.configuration.decoration_color
        decoration_char = self.configuration.decoration_character
        left_decoration_length = self._whole_decoration_line_width() / 2

        return colored(left_decoration_length * decoration_char,
                       color=decoration_color)

    def right_decoration(self):
        decoration_color = self.configuration.decoration_color
        decoration_char = self.configuration.decoration_character
        right_decoration_length = int(
            math.ceil(float(self._whole_decoration_line_width()) / 2))

        return colored(right_decoration_length * decoration_char,
                       color=decoration_color)

    def multi_line_decoration(self):
        if self.configuration.has_multi_line_decoration:
            decoration_char = self.configuration.decoration_character
            decoration_color = self.configuration.decoration_color
            line_width = get_columns()
            return colored(os.linesep +
                           (decoration_char * line_width) +
                           os.linesep,
                           color=decoration_color)

        return os.linesep

    def test_result(self):
        result_text = self._test_result_uncolored()
        result_color = self.configuration.test_result_color
        return colored(result_text, color=result_color)

    def test_name(self):
        name = self._test_name_uncolored()
        color = self.configuration.test_name_color
        return colored(name, color=color)

    def test_type(self):
        test_type = self._test_type_uncolored()
        color = self.configuration.test_type_color
        return colored(test_type, color=color, attrs=["bold"])

    def _test_type_uncolored(self):
        test_types = {
            TestBlock: "Block",
            TestFlow: "Flow",
            TestCase: "Case",
            TestSuite: "Suite"
        }

        for test_type, representation in test_types.iteritems():
            if isinstance(self.test, test_type):
                return representation

        raise TypeError("Can't pretty print test %r, "
                        "unsupported type" % self.test)

    def _test_name_uncolored(self):
        return self.test.data.name

    def _test_result_uncolored(self):
        return str(self.result).capitalize()

    def _whole_decoration_line_width(self):
        """Return the width of the whole decoration line.

       That means the left and right decoration combined, to be used for
       calculating the left and right decorations.

            Returns:
                int. width of the whole decoration line together.

            Note:
                There is a need to calculate left and right decoration
                differently because it is desired to fill the entire screen
                even if the screen width is uneven.
        """
        no_decoration_template = " {test_type}: {test_name} ({result}) "
        text_without_colors = no_decoration_template.format(
            test_type=self._test_type_uncolored(),
            test_name=self._test_name_uncolored(),
            result=self._test_result_uncolored()
        )

        console_width = get_columns()
        return console_width - len(text_without_colors)


def get_columns():
    """Return the amount of columns in the current terminal.

    Returns:
        int. width of a single row in the current terminal.
    """
    if sys.platform in ("linux", "linux2", "darwin"):
        # Both OS X (darwin) and Linux support the 'stty' command
        try:
            _, columns = os.popen("stty size 2>/dev/null").read().split()
            columns = int(columns)
            return columns

        except ValueError:
            # This occurs when using Docker or any platform
            # that doesn't initially render its terminal window.
            return 80

    if sys.platform == "win32":
        from ctypes import windll, create_string_buffer
        stderr_handle = windll.kernel32.GetStdHandle(STDERR_HANDLE_NUMBER)
        info_buffer = create_string_buffer(CSBI_BUFFER_SIZE)
        result = windll.kernel32.GetConsoleScreenBufferInfo(stderr_handle,
                                                            info_buffer)
        if result:
            parsed_result = struct.unpack("hhhhHhhhhhh", info_buffer.raw)
            (_, _, _, _, _, left, _, right, _, _, _) = parsed_result
            return right - left + 1

    # Return default terminal width
    return 80
