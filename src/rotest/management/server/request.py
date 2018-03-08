"""Define a resource manager request."""
# pylint: disable=too-few-public-methods
import time


class Request(object):
    """Holds all details, needed by resource manager to execute a request.

    Attributes:
        worker (Worker): a worker to work with.
        message (AbstractMessage): a message to execute.
    """
    def __init__(self, worker, message, is_server_request=False):
        """Construct the request.

        Args:
            worker (Worker): a worker to work with.
            message (AbstractMessage): a message to execute.
            server_request (bool): flag determine whether the request is a
                client request or an inner server request.
        """
        self.worker = worker
        self.message = message
        self.server_request = is_server_request

        self.creation_time = time.time()

    def __repr__(self):
        return "Request by %r: %r" % (self.worker.name, self.message)

    def respond(self, reply):
        """Sends the reply to the client if possible.

        Args:
            reply (AbstractReply): a reply from the resource manager.
        """
        if not self.server_request and self.worker.is_alive:
            self.worker.respond(reply)
