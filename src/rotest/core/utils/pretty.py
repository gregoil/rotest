"""Utils module for pretty-printing the logs."""
import os
import sys
import math
import struct
from abc import ABCMeta, abstractmethod

import enum
from termcolor import colored

from rotest.core.case import TestCase
from rotest.core.flow import TestFlow
from rotest.core.suite import TestSuite
from rotest.core.block import TestBlock


class TitleConfiguration(object):
    """Interface for specifying the colors that will be printed in a test.

    Attributes:
        result (TestResult): result of the test.
    """
    __metaclass__ = ABCMeta

    def __init__(self, result):
        self.result = result

    @abstractmethod
    def decoration_character(self):
        """Define the character that will be used to decorate the test.

        Returns:
            str. character to be printed in the log.
        """
        pass

    @abstractmethod
    def decoration_color(self):
        """Define the color of the decoration.

        Returns:
            str. name of the color to color the decoration.
        """
        pass

    @abstractmethod
    def test_type_color(self):
        """Define the color of the test type.

        Returns:
            str. name of the color to color the test type("Block"/"Flow")
        """
        pass

    @abstractmethod
    def test_name_color(self):
        """Define the color of the test's name.

        Returns:
            str. name of the color to color the test name.
        """
        pass

    @abstractmethod
    def has_multi_line_decoration(self):
        """Determine whether or not this test has a multi-line decoration.

        Returns:
            bool. True if this tests has multiple lines of decoration.
        """
        pass

    @abstractmethod
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

        else:
            return NonComplexTitleConfiguration(result)


class NonComplexTitleConfiguration(TitleConfiguration):
    def has_multi_line_decoration(self):
        return False

    def decoration_character(self):
        return "-"

    def decoration_color(self):
        colors = {
            TestResult.failure: "red",
            TestResult.error: "red",
            TestResult.skip: "white",
            TestResult.success: "green",
            TestResult.started: "white",
        }

        return colors[self.result]

    def test_type_color(self):
        colors = {
            TestResult.failure: "red",
            TestResult.error: "red",
            TestResult.skip: "white",
            TestResult.success: "green",
            TestResult.started: "white",
        }

        return colors[self.result]

    def test_result_color(self):
        colors = {
            TestResult.failure: "red",
            TestResult.error: "red",
            TestResult.skip: "white",
            TestResult.success: "green",
            TestResult.started: "white",
        }

        return colors[self.result]

    def test_name_color(self):
        colors = {
            TestResult.failure: "red",
            TestResult.error: "red",
            TestResult.skip: "yellow",
            TestResult.success: "green",
            TestResult.started: "cyan"
        }
        return colors[self.result]


class ComplexTitleConfiguration(TitleConfiguration):
    def has_multi_line_decoration(self):
        return True

    def decoration_character(self):
        return "="

    def decoration_color(self):
        colors = {
            TestResult.failure: "red",
            TestResult.error: "red",
            TestResult.skip: "white",
            TestResult.success: "green",
            TestResult.started: "white",
        }

        return colors[self.result]

    def test_result_color(self):
        colors = {
            TestResult.failure: "red",
            TestResult.error: "red",
            TestResult.skip: "white",
            TestResult.success: "green",
            TestResult.started: "white",
        }

        return colors[self.result]

    def test_type_color(self):
        colors = {
            TestResult.failure: "red",
            TestResult.error: "red",
            TestResult.skip: "white",
            TestResult.success: "green",
            TestResult.started: "white",
        }

        return colors[self.result]

    def test_name_color(self):
        colors = {
            TestResult.failure: "red",
            TestResult.error: "red",
            TestResult.skip: "yellow",
            TestResult.success: "green",
            TestResult.started: "blue"
        }
        return colors[self.result]


class TestResult(enum.Enum):
    success = "success"
    skip = "skip"
    error = "error"
    failure = "fail"
    started = "started"
    block_started = "block-started"
    flow_started = "flow-started"

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return str(self) == other


class Pretty(object):
    """Title with decoration.

    Attributes:
        test (AbstractTest): encapsulated test to generate it's title.
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
        decoration_color = self.configuration.decoration_color()
        decoration_char = self.configuration.decoration_character()
        left_decoration_length = self._whole_decoration_line_width() / 2

        return colored(left_decoration_length * decoration_char,
                       decoration_color)

    def right_decoration(self):
        decoration_color = self.configuration.decoration_color()
        decoration_char = self.configuration.decoration_character()
        right_decoration_length = int(
            math.ceil(float(self._whole_decoration_line_width()) / 2))

        return colored(right_decoration_length * decoration_char,
                       decoration_color)

    def multi_line_decoration(self):
        if self.configuration.has_multi_line_decoration():
            decoration_char = self.configuration.decoration_character()
            decoration_color = self.configuration.decoration_color()
            line_width = get_columns()
            return colored(os.linesep +
                           (decoration_char * line_width) +
                           os.linesep,
                           decoration_color)

        else:
            return os.linesep

    def test_result(self):
        result_text = self._test_result_uncolored()
        result_color = self.configuration.test_result_color()
        return colored(result_text, color=result_color)

    def test_name(self):
        name = self._test_name_uncolored()
        color = self.configuration.test_name_color()
        return colored(name, color=color)

    def test_type(self):
        test_type = self._test_type_uncolored()
        color = self.configuration.test_type_color()
        return colored(test_type, color=color, attrs=["bold"])

    def _test_type_uncolored(self):
        if isinstance(self.test, TestBlock):
            return "Block"

        if isinstance(self.test, TestFlow):
            return "Flow"

        if isinstance(self.test, TestCase):
            return "Case"

        if isinstance(self.test, TestSuite):
            return "Suite"

        raise TypeError("Can't pretty print test %r, "
                        "unsupported type" % self.test)

    def _test_name_uncolored(self):
        return self.test.__class__.__name__

    def _test_result_uncolored(self):
        return str(self.result).capitalize()

    def _whole_decoration_line_width(self):
        """Return the width of the whole decoration line.
            That means the left and right decoration combined.
            To be used for calculating the left and right decorations.

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
        _, columns = os.popen("stty size").read().split()
        columns = int(columns)
        return columns

    if sys.platform == "win32":
        from ctypes import windll, create_string_buffer
        handle = windll.kernel32.GetStdHandle(-12)  # stderr
        info_buffer = create_string_buffer(22)
        result = windll.kernel32.GetConsoleScreenBufferInfo(handle,
                                                            info_buffer)
        if result:
            parsed_result = struct.unpack("hhhhHhhhhhh", info_buffer.raw)
            (_, _, _, _, _, left, top, right, bottom, _, _) = parsed_result
            return right - left + 1

    # Return default terminal width
    return 80
