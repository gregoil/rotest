"""Tests resource manager ability to work with multiple clients in parallel.

We test the ResourceManager class behavior under different scenarios using
multiple clients.
"""
# pylint: disable=expression-not-assigned,protected-access
# pylint: disable=too-many-public-methods,invalid-name,broad-except
import unittest
from threading import Thread

import django

from rotest.common import core_log
from rotest.management.common.utils import LOCALHOST
from rotest.management.common.errors import ServerError
from rotest.common.colored_test_runner import colored_main
from rotest.management.client.manager import ClientResourceManager
from rotest.management.models.ut_models import DemoResource, DemoResourceData
from rotest.tests.management.resource_base_test import \
                                            BaseResourceManagementTest
from rotest.management.common.resource_descriptor import \
                                            ResourceDescriptor as Descriptor


class AbstractManagerParallelCase(BaseResourceManagementTest):
    """Abstract TestCase for parallel resource manager test.

    Attributes:
        ACTION_TIMEOUT (number): time to wait for respond from the server.
        SERVER_STARTUP_TIME (number): time to wait until server is up.
        SERVER_ERROR_CODE (number): error code indicating a known server error.
        TIMEOUT_ERROR_CODE (number): error code indicating no response from the
            server.
        UNSPECIFIED_ERROR_CODE (number): error code indicating an unknown
            server error.
    """
    fixtures = ['resource_ut.json']

    ACTION_TIMEOUT = 5

    SERVER_ERROR_CODE = -2
    TIMEOUT_ERROR_CODE = -1
    UNSPECIFIED_ERROR_CODE = -3

    RESOURCE1_NAME = 'available_resource1'
    RESOURCE2_NAME = 'available_resource2'

    def build_action_thread(self, action, client, *params):
        """Create independent thread that run the action & store the result.

        In order to run in parallel, actions should run in different threads.
        The given action will be wrapped by an independent thread to be later
        executed with all the other action threads that should run in parallel.

        Args:
            action (method): action to execute in the thread.
            client (ClientResourceManager): client who perform the action.
            params (tuple): action's arguments.

        Returns:
            Thread. an execution thread of the action.
        """
        def client_action(action, client, *params):
            """Execute client's action and store the result."""
            client.result = self.TIMEOUT_ERROR_CODE

            try:
                core_log.debug("Executing action %r on client %r.",
                               action.__name__, client)
                client.result = action(client, *params)
                core_log.debug("Action %r on client %r was executed.",
                               action.__name__, client)

            except ServerError as ex:
                core_log.debug("ServerError occurred while running action "
                               "%r on client %r. Error was: %s",
                               action.__name__, client, ex)
                client.result = self.SERVER_ERROR_CODE

            except Exception as ex:
                core_log.debug("An error occurred while running action %r on "
                           "client %r. Error type: '%s'. Error was: %s",
                           action.__name__, client, ex.__class__.__name__, ex)
                client.result = self.UNSPECIFIED_ERROR_CODE

        return Thread(target=client_action, args=(action, client) + params)

    @staticmethod
    def execute_threads_and_wait(threads, timeout):
        """Execute the threads and waits until they'll finish their jobs.

        Args:
            threads (list): list of Thread to be execute.
            timeout (number): seconds to wait for each thread to finish.
        """
        core_log.debug("executing threads.")
        [thread.start() for thread in threads]
        [thread.join(timeout) for thread in threads]
        core_log.debug("threads execution ended.")


class TwoClientsParallelCase(AbstractManagerParallelCase):
    """Tests the resource-manager when 2 clients works in parallel."""

    def setUp(self):
        """Initialize two clients and connect them to resource manager."""
        super(TwoClientsParallelCase, self).setUp()

        self.client1 = ClientResourceManager(LOCALHOST)
        self.client2 = ClientResourceManager(LOCALHOST)

        self.client1.connect()
        self.client2.connect()

    def tearDown(self):
        """Disconnect the clients from resource manager."""
        self.client1.disconnect()
        self.client2.disconnect()

        super(TwoClientsParallelCase, self).tearDown()

    def execute_on_clients(self, action, timeout, *args):
        """Execute the given action on each client.

        * Builds execution threads of the given action for each client.
        * Starts the threads and waits until they'll finish their jobs.

        Args:
            action (method): the action to be executed.
            timeout (number): seconds to wait for thread to finish.
            args (tuple): arguments for action.
        """
        clients_threads = [self.build_action_thread(action, client, *args)
                           for client in (self.client1, self.client2)]
        self.execute_threads_and_wait(clients_threads, timeout)

    def test_lock_resource(self):
        """Validate parallel attempt to lock the same resource."""
        descriptor = Descriptor(DemoResource, name=self.RESOURCE1_NAME)
        self.execute_on_clients(ClientResourceManager._lock_resources,
                                self.ACTION_TIMEOUT, [descriptor],
                                self.ACTION_TIMEOUT - 1)

        resource = DemoResourceData.objects.get(name=self.RESOURCE1_NAME)
        self.assertFalse(resource.is_available(), "%r should be locked "
                         "but found available" % (self.RESOURCE1_NAME))

        results = [self.client1.result, self.client2.result]
        self.assertEquals(results.count(self.SERVER_ERROR_CODE), 1,
                          "One client should have failed, actual failures %d"
                          % results.count(self.SERVER_ERROR_CODE))

        results.remove(self.SERVER_ERROR_CODE)

        result, = results
        self.assertTrue(isinstance(result, list), "LockResource action should "
                        "return a list, got '%s'" % (type(result)))

        self.assertEqual(len(result), 1, "Only 1 resource should be locked but"
                         " %d resources were locked." % (len(result)))

        locked_resource, = result
        self.assertEqual(locked_resource.name, self.RESOURCE1_NAME,
                         "Expected locked resource name is %r, but got %r"
                         % (self.RESOURCE1_NAME, locked_resource.name))

    def test_lock_different_resources(self):
        """Validate parallel attempt to lock different resources."""
        descriptor1 = Descriptor(DemoResource, name=self.RESOURCE1_NAME)
        thread1 = self.build_action_thread(
                               ClientResourceManager._lock_resources,
                               self.client1, [descriptor1])

        descriptor2 = Descriptor(DemoResource, name=self.RESOURCE2_NAME)
        thread2 = self.build_action_thread(
                               ClientResourceManager._lock_resources,
                               self.client2, [descriptor2])

        self.execute_threads_and_wait([thread1, thread2], self.ACTION_TIMEOUT)

        results = (self.client1.result, self.client2.result)
        expected_names = (self.RESOURCE1_NAME, self.RESOURCE2_NAME)

        for result, expected_name in zip(results, expected_names):
            resource = DemoResourceData.objects.get(name=expected_name)
            self.assertFalse(resource.is_available(), "%r should be "
                             "locked but found available" % expected_name)

            self.assertTrue(isinstance(result, list), "LockResource action "
                            "should return a list, got '%s'" % (type(result)))

            self.assertEqual(len(result), 1, "Only 1 resource should be locked"
                             " but %d resources were locked." % (len(result)))

            self.assertEqual(result[0].name, expected_name,
                             "Expected locked resource name is %r, but got %r"
                             % (expected_name, result[0].name))


class MultipleClientsParallelCase(AbstractManagerParallelCase):
    """Tests the resource-manager when multiple clients works in parallel."""
    NUM_OF_CLIENTS = 10

    def setUp(self):
        """Initialize clients and connect them to the resource manager."""
        super(MultipleClientsParallelCase, self).setUp()

        self.clients = [ClientResourceManager(LOCALHOST) for _
                        in range(self.NUM_OF_CLIENTS)]

        for client in self.clients:
            client.connect()

    def tearDown(self):
        """Disconnect the clients from the resource manager."""
        for client in self.clients:
            client.disconnect()

        super(MultipleClientsParallelCase, self).tearDown()

    def test_multiple_clients(self):
        """Validate parallel execution of actions.

        * Tries to lock one of 2 different resources multiple times.
        * Validates all attempts (except to 2) returned ServerErrors.
        * Validates 2 resources were locked successfully.
        """
        threads = []
        available_resources = [self.RESOURCE1_NAME, self.RESOURCE2_NAME]

        for client in self.clients:
            descriptor = Descriptor(DemoResource,
                                    name__contains="available_resource")
            action_thread = self.build_action_thread(
                                ClientResourceManager._lock_resources,
                                client, [descriptor],
                                self.ACTION_TIMEOUT - 1)
            threads.append(action_thread)

        self.execute_threads_and_wait(threads, self.ACTION_TIMEOUT)

        results = [client.result for client in self.clients]

        expected_errors_count = self.NUM_OF_CLIENTS - len(available_resources)
        server_error_failures = results.count(self.SERVER_ERROR_CODE)
        self.assertEquals(server_error_failures, expected_errors_count,
                          "Expected %d ServerError failures, found %d."
                          % (expected_errors_count, server_error_failures))

        results.remove(self.SERVER_ERROR_CODE)

        resources_names = [resources[0].name for resources in results
                           if isinstance(resources, list) is True]
        self.assertEquals(set(resources_names), set(available_resources),
                          "Not all resources were locked as expected.")


class ResourceManagementParallelSuite(unittest.TestSuite):
    """A test suite for parallel tests."""
    TESTS = [TwoClientsParallelCase,
             MultipleClientsParallelCase]

    def __init__(self):
        """Construct the class."""
        super(ResourceManagementParallelSuite, self).__init__(
                            unittest.makeSuite(test) for test in self.TESTS)


if __name__ == '__main__':
    django.setup()
    colored_main(defaultTest='ResourceManagementParallelSuite')
