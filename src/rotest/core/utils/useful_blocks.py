"""Module containing some common useful blocks."""
from cached_property import cached_property

from rotest.core.result.result import get_result_handlers
from rotest.core.result.monitor.monitor import AbstractMonitor
from rotest.core.block import TestBlock, MODE_FINALLY, BlockInput, BlockOutput


def unregister_monitor(monitor, result):
    """Stop and unregister the monitor from the result object."""
    if monitor in result.result_handlers:
        monitor.stop_test(monitor.main_test)
        monitor.stop_test_run()
        result.result_handlers.remove(monitor)


class StartMonitorBlock(TestBlock):
    """Block that starts a monitor in the scope of the containing main flow.

    The monitor will behave exactly like one that was registered as an output
    handler, but only on the main flow containing this block.
    The monitor will stop automatically when the flow ends, but you can stop
    it manually if needed with the 'StopMonitorBlock'.
    """
    monitor_name = BlockInput()

    monitor_instance = BlockOutput()

    @cached_property
    def all_result_handlers(self):
        """Get all result handlers.

        Returns:
            dict. all possible result handlers, name -> class.
        """
        return get_result_handlers()

    def remove_monitor(self):
        """Remove the monitor if it's still registered."""
        unregister_monitor(self.monitor_instance, self.result)

    def test_method(self):
        """Find and start the monitor with the given name."""
        monitor_class = self.all_result_handlers.get(self.monitor_name)
        if monitor_class is None:
            raise RuntimeError("No such monitor {!r}".format(
                                                            self.monitor_name))

        if not issubclass(monitor_class, AbstractMonitor):
            raise RuntimeError("{!r} output handler is not a monitor".format(
                                                            self.monitor_name))

        # Get main flow
        self.main_flow = self
        while not self.main_flow.is_main:
            self.main_flow = self.main_flow.parent

        self.monitor_instance = monitor_class(stream=self.result.stream,
                                              main_test=self.main_flow,
                                              descriptions=None)

        self.result.result_handlers.append(self.monitor_instance)
        self.main_flow.addCleanup(self.remove_monitor)

        # Simulate the normal beginning of monitor lifecycle
        self.monitor_instance.start_test_run()
        self.monitor_instance.start_test(self.main_flow)
        self.monitor_instance.setup_finished(self.main_flow)


class StopMonitorBlock(TestBlock):
    """Block that stops a manually started monitor and unregisters it."""
    monitor_instance = BlockInput()

    def test_method(self):
        """Stop the manually started monitor."""
        self.monitor_instance.start_teardown(self.monitor_instance.main_test)
        unregister_monitor(self.monitor_instance, self.result)
