"""Base stream handler."""
# pylint: disable=invalid-name,too-few-public-methods,arguments-differ
# pylint: disable=too-many-arguments,super-init-not-called
from termcolor import colored

from rotest.common.constants import BOLD, RED, BLUE, CYAN, YELLOW
from rotest.core.result.handlers.abstract_handler import AbstractResultHandler

NEW_LINE = '\n'


class ColorStream(object):
    """Colored stream.

    Wraps the given stream write methods with a color characters.

    Attributes:
        stream (object): stream object.
    """
    def __init__(self, stream):
        self.stream = stream

    def write(self, message='', color=None, *attrs):
        """Write the given message with the given color.

        Args:
            message (str): message to write.
            color (str): color for the given message.
            attrs (list): list of additional attributes to use, e.g. 'bold'.
        """
        self.stream.write(colored(message, color, attrs=attrs))
        self.stream.flush()

    def writeln(self, message='', color=None, *attrs):
        """Write the colored message with a new line postfix.

        Args:
            message (str): message to write.
            color (str): color for the given message.
            attrs (list): list of additional attributes to use, e.g. 'bold'.
        """
        self.write(message + NEW_LINE, color, *attrs)


class BaseStreamHandler(AbstractResultHandler):
    """Base stream result handler.

    Implements the common stream handler methods.
    """
    INDENTATION = '  '
    SEPERATOR1 = '=' * 70
    SEPERATOR2 = '-' * 70

    def __init__(self, main_test, stream, descriptions=True):
        """Initialize the handler.

        Args:
            main_test (TestSuite / TestCase): the main test instance.
            stream (object): stream handler of the result.
            descriptions (bool): determines whether or not to include test
                descriptors.
        """
        super(BaseStreamHandler, self).__init__(main_test)
        self.descriptions = descriptions
        self.stream = ColorStream(stream)

    def write_details(self, details_str, indentation=0, color=None, *attrs):
        """Write the test details to the stream.

        Args:
            details_str (str): the test's details.
            indentation (number): test's depth.
            color (str): color to use.
            attrs (list): list of additional attributes to use, e.g. 'bold'.
        """
        indentation_str = indentation * self.INDENTATION
        indented_details = indentation_str + details_str.replace(NEW_LINE,
                                                NEW_LINE + indentation_str)
        self.stream.writeln(indented_details, color, *attrs)

    def print_error_list(self, flavour, errors, color, *attrs):
        """Print a summary of the given error list to the stream.

        Args:
            flavour (str): error type (e.g fail / error / skip...).
            errors (list): error details list.
            color (str): color for the given error.
            attrs (list): list of additional attributes to use, e.g. 'bold'.
        """
        for test, err in errors:
            self.stream.writeln(self.SEPERATOR1)
            self.stream.writeln("%s: %s" % (flavour, test.data.name),
                                color, *attrs)
            self.stream.writeln(self.SEPERATOR2)
            self.stream.writeln("%s" % err)

    def print_errors(self, tests_run, errors, skipped, failures,
                     expected_failures, unexpected_successes):
        """Print a summary of all the given error lists to the stream.

        Args:
            tests_run (number): number of tests run.
            errors (list): error tests details list.
            skipped (list): skipped tests details list.
            failures (list): failures tests details list.
            expected_failures (list): expected failures tests details list.
            unexpected_successes (list): unexpected successes tests details
                list.
        """
        unexpected_successes = ((x, '') for x in unexpected_successes)

        self.stream.writeln()
        self.print_error_list('UNEXPECTED SUCCESS', unexpected_successes, BLUE)
        self.print_error_list('EXPECTED FAILURE', expected_failures, CYAN)
        self.print_error_list('SKIPPED', skipped, YELLOW)
        self.print_error_list('FAIL', failures, RED)
        self.print_error_list('ERROR', errors, RED, BOLD)
