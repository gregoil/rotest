"""Signals usage in Rotest."""
import sys
import signal


class BreakPointException(Exception):
    """An exception to raise on the break signal."""


def raise_exception_handler(_signum, _frame):
    """Raise a break-point exception."""
    raise BreakPointException()


def register_break_signal(_tests, config):
    """Register raising an exception on break signal if needed.

    Args:
        config (attrdict): run configuration.
    """
    if config.debug:
        if sys.platform == "win32":
            signal.signal(signal.SIGBREAK, raise_exception_handler)

        else:
            signal.signal(signal.SIGQUIT, raise_exception_handler)
