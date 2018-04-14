"""Monitor module.

Implement monitors and use them as output handlers to monitor background
processes, statuses and resources.
"""
# pylint: disable=broad-except
from functools import wraps

from rotest.core.case import TestCase
from rotest.core.flow import TestFlow
from rotest.core.block import TestBlock
from rotest.core.result.monitor.server import MonitorServer
from rotest.core.result.handlers.abstract_handler import AbstractResultHandler


class MonitorFailure(AssertionError):
    """Failure error that is raised by monitors."""
    pass


def require_attr(resource_type):
    """Avoid running the decorated method if the test lacks an attribute.

    Args:
        resource_type (str): name of the attribute to search.
    """
    def require_resource_wrapper(func):
        @wraps(func)
        def wrapped_func(self, test, *args, **kwargs):
            if not hasattr(test, resource_type):
                return

            return func(self, test, *args, **kwargs)

        return wrapped_func

    return require_resource_wrapper


def skip_if_case(func):
    """Avoid running the decorated method if the test is a TestCase."""
    @wraps(func)
    def wrapped_func(self, test, *args, **kwargs):
        if isinstance(test, TestCase):
            return

        return func(self, test, *args, **kwargs)

    return wrapped_func


def skip_if_flow(func):
    """Avoid running the decorated method if the test is a TestFlow."""
    @wraps(func)
    def wrapped_func(self, test, *args, **kwargs):
        if isinstance(test, TestFlow):
            return

        return func(self, test, *args, **kwargs)

    return wrapped_func


def skip_if_block(func):
    """Avoid running the decorated method if the test is a TestBlock."""
    @wraps(func)
    def wrapped_func(self, test, *args, **kwargs):
        if isinstance(test, TestBlock):
            return

        return func(self, test, *args, **kwargs)

    return wrapped_func


class AbstractMonitor(AbstractResultHandler):
    """Abstract monitor class.

    A monitor is an output handler that uses tests' attributes, like resources.
    There are two kinds of monitors:
    1. basic monitors - react to the test's event - start, finish, error, etc.
    2. cyclic monitors - run periodically in the background during the test.

    To implement a cyclic monitor, override 'run_monitor' and specify 'CYCLE',
    if not implemented, the monitor will be a basic one (cyclic monitors can
    react to tests' event too).

    Attributes:
        CYCLE (number): sleep time in seconds between monitor runs.
        SINGLE_FAILURE (bool): whether to continue running the monitor after
            it had failed or not.

    Note:
        When running in multiprocess, regular output handlers will be used by
        the main process, and the monitors will be run by each worker,
        since they use tests' attributes (resources, for example) that aren't
        available in the main process.
    """
    SINGLE_FAILURE = True
    CYCLE = NotImplemented

    def __init__(self, *args, **kwargs):
        super(AbstractMonitor, self).__init__(*args, **kwargs)
        self._failed = False

    def run_monitor(self, test):
        """The monitor main procedure."""
        pass

    def safe_run_monitor(self, test):
        """Wrapper for run_monitor that prevents errors and multiple fails."""
        if self._failed and self.SINGLE_FAILURE:
            return

        try:
            self.run_monitor(test)

        except Exception:
            self._failed = True
            test.logger.exception("Got an error while running monitor %r",
                                  self.NAME)

    def setup_finished(self, test):
        """Handle test start event - register the monitor.

        Args:
            test (object): test item instance.
        """
        # Don't register a thread if the monitor doesn't override 'run_monitor'
        if self.run_monitor.im_func is AbstractMonitor.run_monitor.im_func or \
                self.CYCLE is NotImplemented:

            return

        if isinstance(test, TestCase) or \
                (isinstance(test, TestFlow) and test.is_main):
            test.logger.debug("Registering monitor %r", self.NAME)
            self._failed = False
            MonitorServer.register_monitor(self, test)

    def start_teardown(self, test):
        """Handle test teardown event - unregister the monitor.

        Args:
            test (object): test item instance.
        """
        if isinstance(test, TestCase) or \
                (isinstance(test, TestFlow) and test.is_main):

            test.logger.debug("Unregistering monitor %r", self.NAME)
            MonitorServer.unregister_monitor(self)

    def fail_test(self, test, message):
        """Add a monitor failure to the test without stopping it.

        Args:
            test (object): test item instance.
            message (str): failure message.
        """
        if self._failed and self.SINGLE_FAILURE:
            return

        self._failed = True
        failure = MonitorFailure("%s: %s" % (self.NAME, message))
        test.result.addFailure(test, (failure.__class__, failure, None))


class AbstractResourceMonitor(AbstractMonitor):
    """Abstract cyclic monitor that depends on a resource to run.

    This class extends the AbstractMonitor behavior and also waits for the
    resource to be ready for work before starting the monitoring process.

    Attributes:
        RESOURCE_NAME (str): expected field name of the resource in the test.
    """
    RESOURCE_NAME = NotImplemented

    def safe_run_monitor(self, test):
        """Wrapper for run_monitor that also waits for the resource."""
        if hasattr(test, self.RESOURCE_NAME):
            super(AbstractResourceMonitor, self).safe_run_monitor(test)
