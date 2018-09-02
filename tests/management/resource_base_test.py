"""Abstract TestCase for all resources related tests."""
# pylint: disable=attribute-defined-outside-init
# pylint: disable=too-many-public-methods,invalid-name
import time
from threading import Thread, current_thread

from django.test.testcases import TransactionTestCase

from rotest.core.result.result import Result
from rotest.core.result.handlers.db_handler import DBHandler
from rotest.management.server.main import ResourceManagerServer
from rotest.management.models.ut_models import (DemoResource,
                                                DemoComplexResource)


class BaseResourceManagementTest(TransactionTestCase):
    """Abstract TestCase for resources related tests.

    Allow multiple access to the DB from different threads by deriving from
    TransactionTestCase. Every test that use resource manager directly or
    indirectly (using Case) should run the server before it starts. Deriving
    from this class will start the resource manager server in an independent
    thread on the setUp of each test and stop in on the tearDown.
    """
    SERVER_STARTUP_TIME = 0.5

    def setUp(self):
        """Start ResourceManagerServer in an independent thread."""
        self.server = ResourceManagerServer(log_to_screen=False)
        self._server_thread = Thread(target=self.server.start)

        self._server_thread.start()
        time.sleep(self.SERVER_STARTUP_TIME)

    def tearDown(self):
        """Stop resource manager server."""
        self.server.stop()
        self._server_thread.join()

    @staticmethod
    def create_result(main_test):
        """Create a result object for the test and starts it.

        Args:
            main_test(TestSuite / TestCase): the test to be ran.

        Returns:
            Result. a new initiated result object.
        """
        result = Result(outputs=[DBHandler.NAME], main_test=main_test)
        result.startTestRun()
        return result


class ThreadedResource(DemoResource):
    """A UT resource that initializes in another thread."""
    THREADS = []

    def validate(self):
        """Mock validate, register the thread and wait for another."""
        self.THREADS.append(current_thread().ident)
        while len(self.THREADS) <= 1:
            time.sleep(0.1)

    def initialize(self):
        pass

    def finalize(self):
        pass


class ThreadedParent(DemoComplexResource):
    """Fake complex resource class, used in multithreaded resource tests.

    Attributes:
        demo1 (ThreadedResource): sub resource pointer.
        demo2 (ThreadedResource): sub resource pointer.
    """
    PARALLEL_INITIALIZATION = True

    def create_sub_resources(self):
        """Return an iterable to the complex resource's sub-resources."""
        self.demo1 = ThreadedResource(data=self.data.demo1)
        self.demo2 = ThreadedResource(data=self.data.demo2)
        return (self.demo1, self.demo2)

    def initialize(self):
        pass

    def validate(self):
        pass

    def finalize(self):
        pass
