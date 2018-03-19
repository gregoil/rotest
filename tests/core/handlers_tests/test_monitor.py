"""Test Rotest's Monitor class behavior."""
import time
import unittest
import threading

import django

from rotest.core.case import request
from rotest.common.colored_test_runner import colored_main
from rotest.management.models.ut_models import DemoResource
from rotest.core.result.monitor import AbstractMonitor, AbstractResourceMonitor

from tests.core.utils import (MockCase,
                              MockTestSuite,
                              BasicRotestUnitTest)

COMMON_LIST = []
RESOURCE_NAME = 'available_resource1'


class SuccessShortMonitor(AbstractMonitor):
    """Monitor with short cycle."""
    CYCLE = 0.2

    def run_monitor(self, test):
        COMMON_LIST.append(threading.current_thread())


class SuccessLongMonitor(AbstractMonitor):
    """Monitor with cycle longer than the test."""
    CYCLE = 5.0

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
    RESOURCE_NAME = 'no_resource'

    def run_monitor(self, test):
        COMMON_LIST.append(threading.current_thread())


class TempLongSuccessCase(MockCase):
    """Test that waits a while and then passes."""
    __test__ = False

    resources = (request('test_resource', DemoResource, name=RESOURCE_NAME),)

    WAIT_TIME = 0.5

    def test_method(self):
        """Wait a while and then pass."""
        time.sleep(self.WAIT_TIME)


class AbstractTestMonitor(BasicRotestUnitTest):
    """Abstract class for testing monitors."""
    __test__ = False

    fixtures = ['resource_ut.json']

    def setUp(self):
        """Clear global COMMON_LIST."""
        super(AbstractTestMonitor, self).setUp()
        while COMMON_LIST:
            COMMON_LIST.pop()

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


class TestShortCycle(AbstractTestMonitor):
    """Test that monitor with a short cycle is called many times."""
    __test__ = True
    RESULT_OUTPUTS = [SuccessShortMonitor]

    def test_method(self):
        """."""
        self._run_case(TempLongSuccessCase)

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


class TestLongCycle(AbstractTestMonitor):
    """Test that monitor with a too long cycle is called only one time."""
    __test__ = True
    RESULT_OUTPUTS = [SuccessLongMonitor]

    def test_method(self):
        """."""
        self._run_case(TempLongSuccessCase)

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


class TestNoCycle(AbstractTestMonitor):
    """Test that monitor with no cycle defined is not called."""
    __test__ = True
    RESULT_OUTPUTS = [SuccessNonMonitor]

    def test_method(self):
        """."""
        self._run_case(TempLongSuccessCase)

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


class TestSingleFailure(AbstractTestMonitor):
    """Test that monitor that allows a single failure only fails once."""
    __test__ = True
    RESULT_OUTPUTS = [FailingOnceShortMonitor]

    def test_method(self):
        """."""
        self._run_case(TempLongSuccessCase)

        self.assertFalse(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        fail_nums = len(self.result.failures)
        print self.result.failures
        self.assertEqual(fail_nums, 1,
                         "Unexpected number of failures, expected %d got %d" %
                         (1, fail_nums))

        monitor_thread = COMMON_LIST[0]
        self.assertFalse(monitor_thread.is_alive(),
                         "Monitor thread is still alive after the test")


class TestMultipleFailure(AbstractTestMonitor):
    """Test that monitor that allows many single failure fails many times."""
    __test__ = True
    RESULT_OUTPUTS = [FailingMuchShortMonitor]

    def test_method(self):
        """."""
        self._run_case(TempLongSuccessCase)

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


class TestGotResourceMonitor(AbstractTestMonitor):
    """Test that resource monitor runs when it gets its resource."""
    __test__ = True
    RESULT_OUTPUTS = [GotResourceMonitor]

    def test_method(self):
        """."""
        self._run_case(TempLongSuccessCase)

        self.assertTrue(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        cycle_nums = len(COMMON_LIST)
        self.assertGreater(cycle_nums, 1,
                           "Unexpected number of cycles, expected more than "
                           "%d got %d" %
                           (1, cycle_nums))


class TestNoResourceMonitor(AbstractTestMonitor):
    """Test that resource monitor doesn't runs when there's no resource."""
    __test__ = True
    RESULT_OUTPUTS = [NoResourceMonitor]

    def test_method(self):
        """."""
        self._run_case(TempLongSuccessCase)

        self.assertTrue(self.result.wasSuccessful(),
                        'Case failed when it should have succeeded')

        cycle_nums = len(COMMON_LIST)
        self.assertEqual(cycle_nums, 0,
                         "Unexpected number of cycles, expected %d got %d" %
                         (0, cycle_nums))


class TestMonitorSuite(unittest.TestSuite):
    """A test suite for monitor's tests."""
    TESTS = [TestShortCycle,
             TestLongCycle,
             TestNoCycle,
             TestSingleFailure,
             TestMultipleFailure,
             TestGotResourceMonitor,
             TestNoResourceMonitor]

    def __init__(self):
        """Construct the class."""
        super(TestMonitorSuite, self).__init__(
                            unittest.makeSuite(test) for test in self.TESTS)


if __name__ == '__main__':
    django.setup()
    colored_main(defaultTest='TestMonitorSuite')
