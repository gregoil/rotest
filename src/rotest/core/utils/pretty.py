"""Utils module for pretty-printing the logs."""
import os
import sys
import struct

from termcolor import colored

from rotest.core.suite import TestSuite
from rotest.core.case import TestCase
from rotest.core.flow import TestFlow
from rotest.core.block import TestBlock

import enum


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


def wrap_title(test, result):
    columns = get_columns()

    test_class = test.__class__.__name__
    if isinstance(test, TestBlock):
        test_type = "Block"
        title_char = "-"
        if result == Result.started:
            result = Result.block_started

    elif isinstance(test, TestFlow):
        test_type = "Flow"
        title_char = "="
        if result == Result.started:
            result = Result.flow_started

    elif isinstance(test, TestCase):
        test_type = "Case"
        title_char = "-"
        if result == Result.started:
            result = Result.block_started

    elif isinstance(test, TestSuite):
        test_type = "Suite"
        title_char = "="
        if result == Result.started:
            result = Result.flow_started

    else:
        raise TypeError("Unsupported type for pretty-logging: %r" % test_class)

    result_to_type_color = {
        Result.failure: "red",
        Result.error: "red",
        Result.skip: "white",
        Result.success: "green",
        Result.block_started: "white",
        Result.flow_started: "white"
    }

    result_to_name_color = {
        Result.failure: "red",
        Result.error: "red",
        Result.skip: "yellow",
        Result.success: "green",
        Result.block_started: "cyan",
        Result.flow_started: "blue"
    }

    name_color = result_to_name_color[result]
    type_color = result_to_type_color[result]

    if result in (Result.block_started, Result.flow_started):
        result = Result.started

    result = str(result)

    text_len_without_colors = (len(test_type) + 2 + len(test_class) +
                               len(result) + 2 + 3)
    abs_len = (columns - text_len_without_colors)
    final_text = "{decore}\n{decoration_left} {test_type}: " \
                 "{test_name} ({result}) {decoration_right}{decore}"
    formatted = final_text.format(
        decoration_left=colored(title_char * (abs_len / 2), color=type_color),
        decoration_right=colored(title_char * ((abs_len if abs_len % 2 == 0
                                                else abs_len + 1) / 2),
                                 color=type_color),
        test_type=colored(test_type, color=type_color, attrs=["bold"]),
        test_name=colored(test_class, color=name_color),
        result=colored(result.capitalize(), color=name_color),
        decore=colored("\n" + (title_char * columns), type_color)
        if test.IS_COMPLEX else ""
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
