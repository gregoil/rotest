"""Worker - handle a session under the resource manager server."""
# pylint: disable=abstract-method,invalid-name,signature-differs
from itertools import count

from twisted.protocols.basic import LineReceiver

from rotest.core.models.run_data import RunData
from rotest.management.server.request import Request
from rotest.management.common.utils import get_host_name
from rotest.management.common.messages import CleanupUser, ParsingFailure
from rotest.management.common.parsers.abstract_parser import ParsingError
from rotest.management.common.resource_descriptor import ResourceDescriptor
from rotest.management.common.utils import (TEST_ID_KEY,
                                            TEST_NAME_KEY,
                                            TEST_SUBTESTS_KEY,
                                            MESSAGE_DELIMITER,
                                            MESSAGE_MAX_LENGTH,
                                            TEST_CLASS_CODE_KEY,
                                            HOST_PORT_SEPARATOR)


class Worker(LineReceiver):
    """Define the server's worker protocol behavior.

    An instance which serves one client and passes the requests from the
    client to the server via a queue. The worker can server either a resources
    requesting client or a results updating client.

    Attributes:
        parser (AbstractParser): messages parser.

        name (str): worker name (unique for the connection).
        all_tests (dict): maps test identifier to test data.
        run_data (RunData): run data of the current run.
        is_alive (bool): the state of the worker.
        main_test (GeneralData): data of the main test of the run.
    """
    parser = NotImplemented

    delimiter = MESSAGE_DELIMITER
    MAX_LENGTH = MESSAGE_MAX_LENGTH
    SKIP_DELTA_MESSAGE = "Previous run passed according to remote DB"

    def __init__(self):
        self.name = None
        self.all_tests = {}
        self.run_data = None
        self.is_alive = False
        self.main_test = None
        self.user_name = None

        self._messages_counter = count()

    def connectionMade(self):
        """Called when a connection is made.

        Defines client resource container.
        """
        self.is_alive = True

        ip_address, port = self.transport.client
        host = get_host_name(ip_address)

        self.user_name = host
        self.name = '%s%s%d' % (host, HOST_PORT_SEPARATOR, port)

        self.factory.logger.debug("Worker: Got new client %r", self.name)

    def connectionLost(self, reason):
        """Called when the connection is shut down.

        Args:
            reason (twisted.python.failure.Failure): The reason the connection
                was lost.
        """
        self.is_alive = False
        self.factory.logger.debug("Worker: Lost a client %r, reason %r",
                                  self.name, reason.getErrorMessage())
        cleanup_message = CleanupUser(user_name=self.name)

        self.factory.logger.debug("Putting user cleanup request in queue")
        request = Request(self, cleanup_message, is_server_request=True)
        self.factory.request_queue.put(request)
        self.factory.logger.debug("Successfully queued the request")

    def lineReceived(self, encoded_message):
        """Handle data received.

        * Decodes the received data to a valid request.
        * Put the request in the server request queue.
        * If the received data fails to parse, a ParsingFailure reply message
          will be sent to the client.

        Args:
            encoded_message (str): The encoded message which was received with
                the delimiter removed.
        """
        self.factory.logger.debug("Worker received: %r", encoded_message)
        try:
            self.factory.logger.debug("Parsing message: %r", encoded_message)
            message = self.parser.decode(encoded_message)

            self.factory.request_queue.put(Request(self, message))
            self.factory.logger.debug("Successfully queued the request")

        except ParsingError as err:
            self.factory.logger.debug("Failed to parse message: %r",
                                      encoded_message)
            reply_message = ParsingFailure(reason=str(err))
            self.respond(reply_message)

    def _create_test_data(self, test_dict):
        """Recursively create the test's datas and add them to 'all_tests'.

        Args:
            tests_tree (dict): containts the hierarchy of the tests in the run.

        Returns:
            GeneralData. the created test data object.
        """
        data_type = test_dict[TEST_CLASS_CODE_KEY]
        test_data = data_type(name=test_dict[TEST_NAME_KEY])
        test_data.run_data = self.run_data
        test_data.save()
        self.all_tests[test_dict[TEST_ID_KEY]] = test_data

        if TEST_SUBTESTS_KEY in test_dict:
            for sub_test_dict in test_dict[TEST_SUBTESTS_KEY]:
                sub_test = self._create_test_data(sub_test_dict)
                test_data.add_sub_test_data(sub_test)
                sub_test.save()

        return test_data

    def initialize_test_run(self, tests_tree, run_data):
        """Initialize the tests run data.

        Args:
            tests_tree (dict): containts the hierarchy of the tests in the run.
            run_data (dict): containts additional data about the run.
        """
        self.run_data = RunData.objects.create(**run_data)
        self.factory.logger.debug("Creating tests data tree")
        self.main_test = self._create_test_data(tests_tree)
        self.run_data.main_test = self.main_test
        self.run_data.user_name = self.user_name
        self.run_data.save()

    def update_run_data(self, run_data):
        """Initialize the tests run data.

        Args:
            run_data (dict): containts additional data about the run.
        """
        RunData.objects.filter(pk=self.run_data.pk).update(**run_data)

    def start_test(self, test_id):
        """Update the test data to 'in progress' state and set the start time.

        Args:
            test_id (number): the identifier of the test.
        """
        test_data = self.all_tests[test_id]
        test_data.start()
        test_data.save()

    def should_skip(self, test_id):
        """Check if the test passed in the last run according to results DB.

        Args:
            test_id (number): the identifier of the test.

        Returns:
            str. skip reason if there is one, None otherwise.
        """
        test_data = self.all_tests[test_id]
        if test_data.should_skip(test_name=test_data.name,
                                 run_data=self.run_data,
                                 exclude_pk=test_data.pk):

            return self.SKIP_DELTA_MESSAGE

        return None

    def stop_test(self, test_id):
        """Finalize the test's data.

        Args:
            test_id (number): the identifier of the test.
        """
        test_data = self.all_tests[test_id]
        test_data.end()
        test_data.save()

    def update_resources(self, test_id, resources):
        """Update the resources list for a test data.

        Args:
            test_id (number): the identifier of the test.
            resources (list): the resources the test used.
        """
        test_data = self.all_tests[test_id]
        test_data.resources.clear()

        for resource_descriptor in resources:
            resource_dict = ResourceDescriptor.decode(resource_descriptor)
            test_data.resources.add(resource_dict.type.objects.get(
                                                   **resource_dict.properties))

        test_data.save()

    def add_test_result(self, test_id, result_code, info):
        """Add a result to the test.

        Args:
            test_id (number): the identifier of the test.
            result_code (number): code of the result as defined in TestOutcome.
            info (str): additional info (traceback / end reason etc).
        """
        test_data = self.all_tests[test_id]
        test_data.update_result(result_code, info)
        test_data.save()

    def start_composite(self, test_id):
        """Update the test data to 'in progress' state and set the start time.

        Args:
            test_id (number): the identifier of the test.
        """
        test_data = self.all_tests[test_id]
        test_data.start()
        test_data.save()

    def stop_composite(self, test_id):
        """Save the composite test's data.

        Args:
            test_id (number): the identifier of the test.
        """
        test_data = self.all_tests[test_id]
        has_succeeded = all(sub_test.success for sub_test in test_data)
        test_data.success = has_succeeded
        test_data.end()
        test_data.save()

    def respond(self, reply):
        """Respond to the client's request.

        * Set a msg_id.
        * Encodes the reply message.
        * Sends the reply to the client.
        """
        reply.msg_id = self._messages_counter.next()
        encoded_reply = self.parser.encode(reply)

        self.factory.logger.debug("Worker reply: %r", encoded_reply)
        self.sendLine(encoded_reply)
