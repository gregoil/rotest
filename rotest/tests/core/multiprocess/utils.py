"""Test utils for multiprocess functionality UT."""
# pylint: disable=no-self-use,too-many-public-methods,invalid-name
import os
import time
from multiprocessing import Process

import psutil

from rotest.core.case import request
from rotest.management.models.ut_models import DemoResource
from rotest.tests.core.utils import (MockCase, MockFlow, SuccessBlock,
                                     MockBlock, IP_ADDRESS1)


class BasicMultiprocessCase(MockCase):
    """Basic case for multiprocess tests.

    Attributes:
        post_timeout_event (Multiprocessing.Event): will be 'set' only if case
            exceeded timeout limits. (will be overridden)
        pid_queue (Multiprocessing.Queue): A queue to store different PIDs
            related to the case. (will be overridden)
        EXTRA_TIME (number): extra time to wait after the timeout.
        TIMEOUT (number): timeout for the test to run. If the timeout elapses,
            the test should be killed.
    """
    TIMEOUT = 1.5  # Seconds.
    EXTRA_TIME = 0.25  # Seconds.

    pid_queue = None
    post_timeout_event = None

    def test_method(self):
        """Add case's PID to a queue and change a constant."""
        self.register_id(os.getpid())

    def wait_for_timeout(self):
        """Wait until timeout expires and set the event."""
        time.sleep(self.TIMEOUT + self.EXTRA_TIME)
        self.post_timeout_event.set()

    def register_id(self, pid):
        """Register an ID to the queue.

        Args:
            pid (number): ID to register.
        """
        self.pid_queue.put(pid)

    def __getstate__(self):
        """Get the state of the instance.

        Since the class variables aren't included in the instance's dict
        (specifically the queues are important here), we add them artificially.

        Returns:
            dict. a dict representing the state of the instance.
        """
        state_dict = dict(self.__dict__)
        state_dict['pid_queue'] = self.pid_queue
        state_dict['post_timeout_event'] = self.post_timeout_event
        return state_dict


class SubprocessCreationCase(BasicMultiprocessCase):
    """Open a subprocess, add worker and subprocess PIDs to a queue."""

    def test_method(self):
        """Open a sub process, and add Case and subprocess PIDs to a queue."""
        super(SubprocessCreationCase, self).test_method()

        self.create_sub_process()

    def create_sub_process(self):
        """Create a sub process and register it to PIDs queue."""
        process = Process(target=time.sleep, args=(20,))
        process.start()
        self.register_id(process.pid)


class ResourceIdRegistrationCase(BasicMultiprocessCase):
    """Saves the ID of the locked resource to a queue."""
    resources = (request('res1', DemoResource, ip_address=IP_ADDRESS1),)

    def test_method(self):
        """Register the resource's ID to the shared queue."""
        self.register_id(id(self.res1))


class TimeoutWithSubprocessCase(SubprocessCreationCase):
    """Test which open a subprocess and wait for timeout."""

    def test_method(self):
        """Test which open a subprocess and sleeps until timeout."""
        super(TimeoutWithSubprocessCase, self).test_method()

        self.wait_for_timeout()


class TimeoutCase(BasicMultiprocessCase):
    """Test whether a test is killed if the timeout elapses."""

    def test_method(self):
        """Sleep longer than the timeout."""
        super(TimeoutCase, self).test_method()

        self.wait_for_timeout()


class SetupTimeoutCase(TimeoutCase):
    """Test that performs a setUp which gets timeout."""

    def setUp(self):
        self.register_id(os.getpid())
        self.wait_for_timeout()


class TearDownTimeoutCase(TimeoutCase):
    """Test that performs a tearDown which gets timeout."""

    def test_method(self):
        self.register_id(os.getpid())

    def tearDown(self):
        self.wait_for_timeout()


class SuicideCase(MockCase):
    """Kill the current process."""

    def test_method(self):
        """Kill the current process."""
        psutil.Process(os.getpid()).kill()


class SetupTimeoutFlow(BasicMultiprocessCase):
    """Test flow that has a too long setup time."""
    TIMEOUT = 1  # Seconds
    EXTRA_TIME = 0.5  # Seconds

    blocks = (SuccessBlock,)

    def setUp(self):
        """Sleep longer than the timeout."""
        time.sleep(self.TIMEOUT + self.EXTRA_TIME)


class SetupCrashFlow(BasicMultiprocessCase):
    """Test flow that crashes on setup."""
    blocks = (SuccessBlock,)

    def setUp(self):
        """Sleep longer than the timeout."""
        psutil.Process(os.getpid()).kill()


class TimeoutBlock(MockFlow):
    """Test flow that has a too long setup time."""
    WAIT_TIME = 1.5  # Seconds

    def test_timeout(self):
        """Sleep longer than the timeout."""
        time.sleep(self.WAIT_TIME)


class BlockTimeoutFlow(MockFlow):
    """Test flow that has a too long setup time."""
    TIMEOUT = 1  # Seconds
    EXTRA_TIME = 0.5  # Seconds

    blocks = (TimeoutBlock,)


class RegisterPidBlock(MockBlock):
    """Test flow that has a too long setup time."""
    inputs = ('pid_queue',)

    pid_queue = None

    def test_register(self):
        """Sleep longer than the timeout."""
        self.pid_queue.put(os.getpid())


class RegisterInSetupFlow(MockFlow):
    """Basic test-flow for multiprocess tests.

    Attributes:
        pid_queue (Multiprocessing.Queue): A queue to store different PIDs
            related to the test. (will be overridden)
    """
    pid_queue = None
    blocks = (RegisterPidBlock,
              RegisterPidBlock)

    def __getstate__(self):
        """Get the state of the instance.

        Since the class variables aren't included in the instance's dict
        (specifically the queues are important here), we add them artificially.

        Returns:
            dict. a dict representing the state of the instance.
        """
        state_dict = dict(self.__dict__)
        state_dict['pid_queue'] = self.pid_queue
        return state_dict

    def setUp(self):
        self.pid_queue.put(os.getpid())
