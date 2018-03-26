"""Utils module for pretty-printing the logs."""
import os
import sys
import math
import struct
from abc import ABCMeta, abstractmethod

import enum
from termcolor import colored


class TitleConfiguration(object):
    """Interface for specifying the colors that will be printed in a test.

    Attributes:
        result (Result): result of the test.
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
            Result.failure: "red",
            Result.error: "red",
            Result.skip: "white",
            Result.success: "green",
            Result.started: "white",
        }

        return colors[self.result]

    def test_type_color(self):
        colors = {
            Result.failure: "red",
            Result.error: "red",
            Result.skip: "white",
            Result.success: "green",
            Result.started: "white",
        }

        return colors[self.result]

    def test_result_color(self):
        colors = {
            Result.failure: "red",
            Result.error: "red",
            Result.skip: "white",
            Result.success: "green",
            Result.started: "white",
        }

        return colors[self.result]

    def test_name_color(self):
        colors = {
            Result.failure: "red",
            Result.error: "red",
            Result.skip: "yellow",
            Result.success: "green",
            Result.started: "cyan"
        }
        return colors[self.result]


class ComplexTitleConfiguration(TitleConfiguration):
    def has_multi_line_decoration(self):
        return True

    def decoration_character(self):
        return "="

    def decoration_color(self):
        colors = {
            Result.failure: "red",
            Result.error: "red",
            Result.skip: "white",
            Result.success: "green",
            Result.started: "white",
        }

        return colors[self.result]

    def test_result_color(self):
        colors = {
            Result.failure: "red",
            Result.error: "red",
            Result.skip: "white",
            Result.success: "green",
            Result.started: "white",
        }

        return colors[self.result]

    def test_type_color(self):
        colors = {
            Result.failure: "red",
            Result.error: "red",
            Result.skip: "white",
            Result.success: "green",
            Result.started: "white",
        }

        return colors[self.result]

    def test_name_color(self):
        colors = {
            Result.failure: "red",
            Result.error: "red",
            Result.skip: "yellow",
            Result.success: "green",
            Result.started: "blue"
        }
        return colors[self.result]


class Result(enum.Enum):
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


def wrap_title(test, result):
    test_name = test.__class__.__name__
    test_type = "What?"  # TODO: Implement this

    result = str(result)

    no_decoration_template = " {test_type}: {test_name} ({result}) "
    text_len_without_colors = len(no_decoration_template.format(**locals()))
    columns = get_columns()
    abs_len = (columns - text_len_without_colors)
    decoration_left_length = abs_len / 2
    decoration_right_length = int(math.ceil(float(abs_len) / 2))

    title_configuration = TitleConfiguration.from_test(test, result)
    decoration_char = title_configuration.decoration_character()
    decoration_color = title_configuration.decoration_color()
    test_type_color = title_configuration.test_type_color()
    test_name_color = title_configuration.test_name_color()
    result_color = title_configuration.test_result_color()

    final_text = "{decore}\n{decoration_left} {test_type}: " \
                 "{test_name} ({result}) {decoration_right}{decore}"
    formatted = final_text.format(
        decoration_left=colored(decoration_char * decoration_left_length,
                                color=decoration_color),
        decoration_right=colored(decoration_char * decoration_right_length,
                                 color=decoration_color),
        test_type=colored(test_type, color=test_type_color, attrs=["bold"]),
        test_name=colored(test_name, color=test_name_color),
        result=colored(result.capitalize(), color=result_color),
        decore=colored("\n" + (decoration_char * columns),
                       decoration_color) if test.IS_COMPLEX else ""
    )

    return formatted


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
