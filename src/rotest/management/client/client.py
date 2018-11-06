"""Define an abstract client."""
# pylint: disable=too-many-arguments,too-many-instance-attributes
from __future__ import absolute_import

from future.builtins import object
from swaggapi.api.builder.client.requester import Requester

from rotest.common import core_log
from rotest.api.request_token import RequestToken
from rotest.api.common.models import GenericModel
from rotest.api.resource_control import UpdateFields
from rotest.api.common import UpdateFieldsParamsModel
from rotest.management.common.parsers import JSONParser
from rotest.api.common.responses import FailureResponseModel
from rotest.management.common.resource_descriptor import ResourceDescriptor
from rotest.common.config import (DJANGO_MANAGER_PORT,
                                  RESOURCE_REQUEST_TIMEOUT, API_BASE_URL)


class AbstractClient(object):
    """Abstract client class.

    Basic requests handling for communicating with the remote server.

    Attributes:
        logger (logging.Logger): resource manager logger.
        lock_timeout (number): default waiting time on requests.
        _host (str): server's host.
        _port (number): server's port.
    """
    REPLY_OVERHEAD_TIME = 2
    _DEFAULT_REPLY_TIMEOUT = 18

    parser = JSONParser()

    def __init__(self, host, port=DJANGO_MANAGER_PORT,
                 base_uri=API_BASE_URL,
                 lock_timeout=RESOURCE_REQUEST_TIMEOUT,
                 logger=core_log):
        """Initialize a socket connection to the server.

        Args:
            host (str): Server's IP address.
            lock_timeout (number): default waiting time on requests.
            logger (logging.Logger): client's logger.
        """
        self._host = host
        self._port = port
        self.base_uri = base_uri
        self.logger = logger
        self.lock_timeout = lock_timeout
        self.token = None
        self.requester = Requester(host=self._host,
                                   port=self._port,
                                   base_url=self.base_uri,
                                   logger=self.logger)

    def connect(self):
        """Connect to manager server."""
        response = self.requester.request(RequestToken,
                                          method="get",
                                          data=GenericModel({}))

        if isinstance(response, FailureResponseModel):
            raise RuntimeError(response.details)

        self.token = response.token

    def is_connected(self):
        """Check if the socket is connected or not.

        Returns:
            bool. True if connection was already made, False otherwise.
        """
        return self.token is not None

    def disconnect(self):
        """Cleanup the client."""
        self.token = None

    def __enter__(self):
        """Connect to manager server."""
        self.connect()
        return self

    def __exit__(self, *args, **kwargs):
        """Disconnect from manager server."""
        self.disconnect()

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

        descriptor = ResourceDescriptor(resource_type=model, **filter_dict)

        request_data = UpdateFieldsParamsModel({
            "resource_descriptor": descriptor.encode(),
            "changes": kwargs
        })
        response = self.requester.request(UpdateFields,
                                          data=request_data,
                                          method="put")

        if isinstance(response, FailureResponseModel):
            raise Exception(response.details)
