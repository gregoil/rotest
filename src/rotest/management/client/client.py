"""Define an abstract client."""
# pylint: disable=too-many-arguments
import socket
from itertools import count

from rotest.common import core_log
from rotest.management.common import messages
from rotest.management.common.errors import ErrorFactory
from rotest.management.common.parsers import DEFAULT_PARSER
from rotest.management.common.parsers.abstract_parser import ParsingError
from rotest.common.config import (RESOURCE_REQUEST_TIMEOUT,
                                  RESOURCE_MANAGER_PORT)
from rotest.management.common.utils import (MESSAGE_DELIMITER,
                                            MESSAGE_MAX_LENGTH)


class AbstractClient(object):
    """Abstract client class.

    Basic requests handling for communicating with the remote server.

    Attributes:
        logger (logging.Logger): resource manager logger.
        lock_timeout (number): default waiting time on requests.
        _host (str): server's host.
        _port (number): server's port.
        _messages_counter (itertools.count): msg_id counter.
        _parser (AbstractParser): messages parser.
    """
    REPLY_OVERHEAD_TIME = 2
    _DEFAULT_REPLY_TIMEOUT = 18

    def __init__(self, host, port=RESOURCE_MANAGER_PORT,
                 parser=DEFAULT_PARSER(),
                 lock_timeout=RESOURCE_REQUEST_TIMEOUT,
                 logger=core_log):
        """Initialize a socket connection to the server.

        Args:
            host (str): Server's IP address.
            port (number): Server's port.
            parser (AbstractParser): parser to parse the messages with.
            lock_timeout (number): default waiting time on requests.
            logger (logging.Logger): client's logger.
        """
        self._host = host
        self._port = port
        self._socket = None
        self.logger = logger
        self._parser = parser
        self._messages_counter = count()
        self.lock_timeout = lock_timeout

    def connect(self, timeout=_DEFAULT_REPLY_TIMEOUT):
        """Connect to manager server.

        Args:
            timeout (number): time to wait for a reply from the server.
        """
        if self._socket is not None:
            self.logger.debug("Ignoring attempt to re-connect to server: %r",
                              self._host)
            return

        self.logger.debug("Connecting to server. Hostname: %r", self._host)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._set_reply_timeout(timeout)
        self._socket.connect((self._host, self._port))

    def is_connected(self):
        """Check if the socket is connected or not.

        Returns:
            bool. True if the socket is connected, False otherwise.
        """
        return self._socket is not None

    def disconnect(self):
        """Disconnect from manager server.

        Raises:
            RuntimeError: wasn't connected in the first place.
        """
        if not self.is_connected():
            raise RuntimeError("Socket was not connected")

        self._socket.close()

    def __enter__(self):
        """Connect to manager server."""
        self.connect()
        return self

    def __exit__(self, *args, **kwargs):
        """Disconnect from manager server."""
        self.disconnect()

    def _set_reply_timeout(self, timeout):
        """Set the reply timeout.

        Args:
            timeout (number): Set the time (in seconds) to wait for a reply
                from the manager server.
        """
        self.logger.debug("Setting client reply timeout to: %s", timeout)

        if timeout is not None:
            timeout += self.REPLY_OVERHEAD_TIME

        self._socket.settimeout(timeout)

    def _wait_for_reply(self):
        """Receive and decode a message from the manager server.

        Returns:
            AbstractMessage. Server reply for given request.
        """
        encoded_reply = ""

        while not encoded_reply.endswith(MESSAGE_DELIMITER):
            encoded_reply += self._socket.recv(MESSAGE_MAX_LENGTH)

        return self._parser.decode(encoded_reply)

    def _request(self, request_msg, timeout=_DEFAULT_REPLY_TIMEOUT):
        """Send a message to manager server and wait for an answer.

        * Encodes the request message and sends it to manager server.
        * Waits for manager server reply message.

        Args:
            request_msg (AbstractMessage): request for manager server.
            timeout (number): the request's waiting timeout.

        Returns:
            AbstractMessage. Server reply for given request.

        Raises:
            TypeError: client received an illegal reply message.
            ParsingError: client failed to decode server's reply.
            ParsingError: server failed to decode client's request.
            RuntimeError: server reply on a different request.
            RuntimeError: server didn't respond, timeout expired.
            ServerError: server failed to execute the request.
        """
        self._set_reply_timeout(timeout)

        request_msg.msg_id = self._messages_counter.next()
        encoded_request = self._parser.encode(request_msg) + MESSAGE_DELIMITER
        sent_bytes = 0

        if len(encoded_request) > MESSAGE_MAX_LENGTH:
            raise RuntimeError("Client error: Trying to send a too long "
                               "message to the server (%d > %d)" %
                               (len(encoded_request), MESSAGE_MAX_LENGTH))

        while sent_bytes < len(encoded_request):
            sent_bytes += self._socket.send(encoded_request[sent_bytes:])

        while True:
            try:
                reply_msg = self._wait_for_reply()

            except socket.timeout:
                raise RuntimeError("Server failed to respond to %r after %r "
                                   "seconds" %
                                   (request_msg, self._socket.gettimeout()))

            if not isinstance(reply_msg, messages.AbstractReply):
                raise TypeError("Server sent an illegal message."
                                "Replies should be of type AbstractReply."
                                "Received message is: %r" % reply_msg)

            if reply_msg.request_id != request_msg.msg_id:
                self.logger.warning("Client expected a reply on message with "
                                    "id %r, got a reply with id %r, ignoring",
                                    request_msg.msg_id, reply_msg.request_id)

                continue

            if isinstance(reply_msg, messages.ParsingFailure):
                raise ParsingError("Server failed to parse a message. "
                                   "Failure Reason is: %r." % reply_msg.reason)

            if isinstance(reply_msg, messages.ErrorReply):
                raise ErrorFactory.build_error(reply_msg.code,
                                               reply_msg.content)

            return reply_msg

    def update_fields(self, model, filter_dict=None, **kwargs):
        """Update content in the server's DB.

        Args:
            model (type): Django model to apply changes on.
            filter_dict (dict): arguments to filter by.
            kwargs (dict): the additional arguments are the changes to apply on
                the filtered instances.
        """
        if filter_dict is None:
            filter_dict = {}

        msg = messages.UpdateFields(model=model,
                                    filter=filter_dict,
                                    kwargs=kwargs)

        self._request(msg)
