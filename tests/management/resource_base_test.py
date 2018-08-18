"""Abstract TestCase for all resources related tests."""
# pylint: disable=too-many-public-methods,invalid-name
import os
import sys
import signal
import subprocess

import time
from django.test.testcases import TransactionTestCase

from rotest.common.config import search_config_file
from rotest.core.result.result import Result
from rotest.core.result.handlers.db_handler import DBHandler


class BaseResourceManagementTest(TransactionTestCase):
    """Abstract TestCase for resources related tests.

    Allow multiple access to the DB from different threads by deriving from
    TransactionTestCase. Every test that use resource manager directly or
    indirectly (using Case) should run the server before it starts. Deriving
    from this class will start the resource manager server in an independent
    thread on the setUp of each test and stop in on the tearDown.
    """
    SERVER_STARTUP_TIME = 5

    @classmethod
    def setUpClass(cls):
        """Start ResourceManagerServer in an independent thread."""
        app_directory = os.path.dirname(search_config_file())
        manage_py_location = os.path.join(app_directory, "manage.py")
        cls.django_process = subprocess.Popen(
            "python {} runserver 0.0.0.0:{}".format(manage_py_location, 8000),
            shell=True)
        time.sleep(cls.SERVER_STARTUP_TIME)

    @classmethod
    def tearDownClass(cls):
        """Stop resource manager server."""
        if sys.platform == 'win32':
            subprocess.call(['taskkill', '/F', '/T', '/PID',
                             str(cls.django_process.pid)])
        else:
            os.kill(cls.django_process.pid, signal.SIGTERM)

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
