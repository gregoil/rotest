"""Test Rotest's Monitor class behavior."""
import time
import threading

from future.builtins import next

from rotest.core.case import request
from rotest.core.flow_component import Pipe
from rotest.management.models.ut_resources import DemoResource
from rotest.core.utils.useful_blocks import StartMonitorBlock, StopMonitorBlock
from rotest.core.result.monitor import AbstractMonitor, AbstractResourceMonitor

from tests.core.utils import (MockCase, MockTestSuite, BasicRotestUnitTest,
                              MockBlock, MockFlow)

COMMON_LIST = []
RESOURCE_NAME = 'available_resource1'


class SuccessShortMonitor(AbstractMonitor):
    """Monitor with short cycle."""
    CYCLE = 0.2

    def run_monitor(self, test):
        COMMON_LIST.append(threading.current_thread())


class SuccessLongMonitor(AbstractMonitor):
    """Monitor with cycle longer than the test."""
    CYCLE = 2.0

    def run_monitor(self, test):
        COMMON_LIST.append(threading.current_thread())


class SuccessNonMonitor(AbstractMonitor):
    """Monitor with no cyclevalue passed."""
    def run_monitor(self, test):
        COMMON_LIST.append(threading.current_thread())


class FailingOnceShortMonitor(AbstractMonitor):
    """Monitor that fails once with short cycle."""
    CYCLE = 0.2
    SINGLE_FAILURE = True

    def run_monitor(self, test):
        COMMON_LIST.append(threading.current_thread())
        self.fail_test(test, "monitor failure")


class FailingMuchShortMonitor(AbstractMonitor):
    """Monitor that fails many times with short cycle.."""
    CYCLE = 0.2
    SINGLE_FAILURE = False

    def run_monitor(self, test):
        COMMON_LIST.append(threading.current_thread())
        self.fail_test(test, "monitor failure")


class GotResourceMonitor(AbstractResourceMonitor):
    """Resource monitor with short cycle."""
    CYCLE = 0.2
    RESOURCE_NAME = 'test_resource'

    def run_monitor(self, test):
        COMMON_LIST.append(threading.current_thread())


class NoResourceMonitor(AbstractResourceMonitor):
    """Resource monitor that expected a non-existing resource."""
    CYCLE = 0.2
    RESOURCE_NAME = 'non_existing_resource'

    def run_monitor(self, test):
        COMMON_LIST.append(threading.current_thread())


class LongSuccessCase(MockCase):
    """Test that waits a while and then passes."""
    __test__ = False

    resources = (request('test_resource', DemoResource, name=RESOURCE_NAME),)

    WAIT_TIME = 0.5

    def test_method(self):
        """Wait a while and then pass."""
        time.sleep(self.WAIT_TIME)


class LongSuccessBlock(MockBlock):
    """Test that waits a while and then passes."""
    __test__ = False

    resources = (request('test_resource', DemoResource, name=RESOURCE_NAME),)

    WAIT_TIME = 0.5

    def test_method(self):
        """Wait a while and then pass."""
        time.sleep(self.WAIT_TIME)


class AbstractMonitorTest(BasicRotestUnitTest):
    """Abstract class for testing monitors."""
    __test__ = False

    fixtures = ['resource_ut.json']

    def setUp(self):
        """Clear global COMMON_LIST."""
        super(AbstractMonitorTest, self).setUp()
        del COMMON_LIST[:]

    def _run_case(self, test_case):
        """Run given case and return it.

        Args:
            test_case (rotest.core.case.TestCase): case to run.

        Returns:
            rotest.core.case.TestCase. the case.
        """
        class InternalSuite(MockTestSuite):
            components = (test_case,)

        test_suite = InternalSuite()
        self.run_test(test_suite)
        return next(iter(test_suite))


class TestShortCycle(AbstractMonitorTest):
    """Test that monitor with a short cycle is called many times."""
    __test__ = True
    RESULT_OUTPUTS = [SuccessShortMonitor]

    def test_method(self):
        self._run_case(LongSuccessCase)

        self.assertTrue(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        fail_nums = len(self.result.failures)
        self.assertEqual(fail_nums, 0,
                         "Unexpected number of failures, expected %d got %d" %
                         (0, fail_nums))

        cycle_nums = len(COMMON_LIST)
        self.assertGreater(cycle_nums, 1,
                           "Unexpected number of cycles, expected more than "
                           "%d got %d" %
                           (1, cycle_nums))

        monitor_thread = COMMON_LIST[0]
        self.assertFalse(monitor_thread.is_alive(),
                         "Monitor thread is still alive after the test")


class TestLongCycle(AbstractMonitorTest):
    """Test that monitor with a too long cycle is called only one time."""
    __test__ = True
    RESULT_OUTPUTS = [SuccessLongMonitor]

    def test_method(self):
        self._run_case(LongSuccessCase)

        self.assertTrue(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        fail_nums = len(self.result.failures)
        self.assertEqual(fail_nums, 0,
                         "Unexpected number of failures, expected %d got %d" %
                         (0, fail_nums))

        cycle_nums = len(COMMON_LIST)
        self.assertEqual(cycle_nums, 1,
                         "Unexpected number of cycles, expected %d got %d" %
                         (1, cycle_nums))

        monitor_thread = COMMON_LIST[0]
        self.assertFalse(monitor_thread.is_alive(),
                         "Monitor thread is still alive after the test")


class TestNoCycle(AbstractMonitorTest):
    """Test that monitor with no cycle defined is not called."""
    __test__ = True
    RESULT_OUTPUTS = [SuccessNonMonitor]

    def test_method(self):
        self._run_case(LongSuccessCase)

        self.assertTrue(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        fail_nums = len(self.result.failures)
        self.assertEqual(fail_nums, 0,
                         "Unexpected number of failures, expected %d got %d" %
                         (0, fail_nums))

        cycle_nums = len(COMMON_LIST)
        self.assertEqual(cycle_nums, 0,
                         "Unexpected number of cycles, expected %d got %d" %
                         (0, cycle_nums))


class TestSingleFailure(AbstractMonitorTest):
    """Test that monitor that allows a single failure only fails once."""
    __test__ = True
    RESULT_OUTPUTS = [FailingOnceShortMonitor]

    def test_method(self):
        self._run_case(LongSuccessCase)

        self.assertFalse(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        fail_nums = len(self.result.failures)

        self.assertEqual(fail_nums, 1,
                         "Unexpected number of failures, expected %d got %d" %
                         (1, fail_nums))

        monitor_thread = COMMON_LIST[0]
        self.assertFalse(monitor_thread.is_alive(),
                         "Monitor thread is still alive after the test")


class TestMultipleFailure(AbstractMonitorTest):
    """Test that monitor that allows many single failure fails many times."""
    __test__ = True
    RESULT_OUTPUTS = [FailingMuchShortMonitor]

    def test_method(self):
        self._run_case(LongSuccessCase)

        self.assertFalse(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        fail_nums = len(self.result.failures)
        self.assertGreater(fail_nums, 1,
                           "Unexpected number of failures, expected more than "
                           "%d got %d" %
                           (1, fail_nums))

        monitor_thread = COMMON_LIST[0]
        self.assertFalse(monitor_thread.is_alive(),
                         "Monitor thread is still alive after the test")


class TestGotResourceMonitor(AbstractMonitorTest):
    """Test that resource monitor runs when it gets its resource."""
    __test__ = True
    RESULT_OUTPUTS = [GotResourceMonitor]

    def test_method(self):
        self._run_case(LongSuccessCase)

        self.assertTrue(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        cycle_nums = len(COMMON_LIST)
        self.assertGreater(cycle_nums, 1,
                           "Unexpected number of cycles, expected more than "
                           "%d got %d" %
                           (1, cycle_nums))


class TestNoResourceMonitor(AbstractMonitorTest):
    """Test that resource monitor doesn't runs when there's no resource."""
    __test__ = True
    RESULT_OUTPUTS = [NoResourceMonitor]

    def test_method(self):
        """."""
        self._run_case(LongSuccessCase)

        self.assertTrue(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        cycle_nums = len(COMMON_LIST)
        self.assertEqual(cycle_nums, 0,
                         "Unexpected number of cycles, expected %d got %d" %
                         (0, cycle_nums))


class TestManuallyStartStopMonitor(AbstractMonitorTest):
    """Test StartMonitorBlock and StopMonitorBlock."""
    __test__ = True
    RESULT_OUTPUTS = []

    def test_no_monitor_supplied(self):
        """Check that an error is raised if no monitor type is given."""
        class DemoFlow(MockFlow):
            blocks = [
                LongSuccessBlock,
                StartMonitorBlock,
                LongSuccessBlock,
            ]
        self._run_case(DemoFlow)

        self.assertFalse(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        cycle_nums = len(COMMON_LIST)
        self.assertEqual(cycle_nums, 0,
                         "Unexpected number of cycles, expected %d got %d" %
                         (0, cycle_nums))

        monitor_thread = COMMON_LIST[0]
        self.assertFalse(monitor_thread.is_alive(),
                         "Monitor thread is still alive after the test")

    def test_short_monitor(self):
        """Check that a short cycle monitor runs more than once."""
        class DemoFlow(MockFlow):
            blocks = [
                LongSuccessBlock,
                StartMonitorBlock.params(monitor_class=SuccessShortMonitor),
                LongSuccessBlock,
                StopMonitorBlock,
            ]
        self._run_case(DemoFlow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        fail_nums = len(self.result.failures)
        self.assertEqual(fail_nums, 0,
                         "Unexpected number of failures, expected %d got %d" %
                         (0, fail_nums))

        cycle_nums = len(COMMON_LIST)
        self.assertGreater(cycle_nums, 1,
                           "Unexpected number of cycles, expected more than "
                           "%d got %d" %
                           (1, cycle_nums))

        monitor_thread = COMMON_LIST[0]
        self.assertFalse(monitor_thread.is_alive(),
                         "Monitor thread is still alive after the test")

    def test_long_monitor_stopped(self):
        """Check that after calling stop the monitor won't run anymore."""
        class DemoFlow(MockFlow):
            blocks = [
                LongSuccessBlock,
                StartMonitorBlock.params(monitor_class=SuccessLongMonitor),
                LongSuccessBlock,
                StopMonitorBlock,  # Stop the monitor
                LongSuccessBlock,
                LongSuccessBlock,
                LongSuccessBlock,
                LongSuccessBlock,
                LongSuccessBlock,
            ]
        self._run_case(DemoFlow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        fail_nums = len(self.result.failures)
        self.assertEqual(fail_nums, 0,
                         "Unexpected number of failures, expected %d got %d" %
                         (0, fail_nums))

        cycle_nums = len(COMMON_LIST)
        self.assertEqual(cycle_nums, 1,
                         "Unexpected number of cycles, expected %d got %d" %
                         (1, cycle_nums))

        monitor_thread = COMMON_LIST[0]
        self.assertFalse(monitor_thread.is_alive(),
                         "Monitor thread is still alive after the test")

    def test_no_stop_monitor(self):
        """Check the monitors automatically stops at the end of the test."""
        class DemoFlow(MockFlow):
            blocks = [
                LongSuccessBlock,
                StartMonitorBlock.params(monitor_class=SuccessShortMonitor),
                LongSuccessBlock,
            ]
        self._run_case(DemoFlow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        fail_nums = len(self.result.failures)
        self.assertEqual(fail_nums, 0,
                         "Unexpected number of failures, expected %d got %d" %
                         (0, fail_nums))

        cycle_nums = len(COMMON_LIST)
        self.assertGreater(cycle_nums, 1,
                           "Unexpected number of cycles, expected more than "
                           "%d got %d" %
                           (1, cycle_nums))

        monitor_thread = COMMON_LIST[0]
        self.assertFalse(monitor_thread.is_alive(),
                         "Monitor thread is still alive after the test")

    def test_multiple_monitors(self):
        """Check you can stop just a specific monitor."""
        class DemoFlow(MockFlow):
            blocks = [
                LongSuccessBlock,
                StartMonitorBlock.params(monitor_class=SuccessShortMonitor,
                                         monitor_instance=Pipe('monitor1')),
                StartMonitorBlock.params(monitor_class=SuccessShortMonitor,
                                         monitor_instance=Pipe('monitor2')),
                LongSuccessBlock,
                StopMonitorBlock.params(monitor_instance=Pipe('monitor1')),
                LongSuccessBlock,
                LongSuccessBlock,
                StopMonitorBlock.params(monitor_instance=Pipe('monitor2')),
            ]
        self._run_case(DemoFlow)

        self.assertTrue(self.result.wasSuccessful(),
                        'Flow failed when it should have succeeded')

        fail_nums = len(self.result.failures)
        self.assertEqual(fail_nums, 0,
                         "Unexpected number of failures, expected %d got %d" %
                         (0, fail_nums))

        self.assertEqual(len(set(COMMON_LIST)), 2,
                         "Unexpected number of monitors ran, "
                         "expected %d got %d" % (2, len(set(COMMON_LIST))))

        monitor1_thread = COMMON_LIST[0]
        monitor2_thread = (set(COMMON_LIST) - {monitor1_thread}).pop()
        monitor1_cycles = COMMON_LIST.count(monitor1_thread)
        monitor2_cycles = COMMON_LIST.count(monitor2_thread)
        self.assertGreater(monitor2_cycles, monitor1_cycles * 2,
                           "Expected unstopped monitor to run more than twice "
                           "the times of the stopped one, got %d and %d" %
                           (monitor2_cycles, monitor1_cycles))

        self.assertFalse(monitor1_thread.is_alive(),
                         "Monitor 1 thread is still alive after the test")

        self.assertFalse(monitor2_thread.is_alive(),
                         "Monitor 2 thread is still alive after the test")
