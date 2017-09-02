"""Abstract TestCase for all resources related tests."""
# pylint: disable=too-many-public-methods,invalid-name
import time
from threading import Thread

from django.test.testcases import TransactionTestCase

from rotest.core.result.result import Result
from rotest.management.common.utils import LOCALHOST
from rotest.core.result.handlers.db_handler import DBHandler
from rotest.management.server.main import ResourceManagerServer
from rotest.management.common.utils import set_resource_manager_hostname


class BaseResourceManagementTest(TransactionTestCase):
    """Abstract TestCase for resources related tests.

    Allow multiple access to the DB from different threads by deriving from
    TransactionTestCase. Every test that use resource manager directly or
    indirectly (using Case) should run the server before it starts. Deriving
    from this class will start the resource manager server in an independent
    thread on the setUp of each test and stop in on the tearDown.
    """
    SERVER_STARTUP_TIME = 0.5

    @classmethod
    def setUpClass(cls):
        """Set the server host to be the localhost.

        This will allow the resource manager server and the
        tests to use the same DB.
        """
        super(BaseResourceManagementTest, cls).setUpClass()

        set_resource_manager_hostname(LOCALHOST)

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
