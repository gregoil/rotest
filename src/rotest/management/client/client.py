"""Define an abstract client."""
# pylint: disable=too-many-arguments,too-many-instance-attributes
from __future__ import absolute_import

import json

from future.builtins import object
from swaggapi.api.builder.client.requester import Requester

from rotest.common import core_log
from rotest.api.request_token import RequestToken
from rotest.api.resource_control import UpdateFields
from rotest.api.common import UpdateFieldsParamsModel
from rotest.api.test_control import GetTestStatistics
from rotest.management.common.parsers import JSONParser
from rotest.api.common.responses import FailureResponseModel
from rotest.management.client.websocket_client import PingingWebsocket
from rotest.api.common.models import GenericModel, StatisticsRequestModel
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

    WEBSOCKET_TARGET = "ws://{host}:{port}/"

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
        self.websocket = PingingWebsocket()
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
        self.websocket.connect(self.WEBSOCKET_TARGET.format(host=self._host,
                                                            port=self._port))

        self.websocket.send(json.dumps({"token": self.token}))

    def is_connected(self):
        """Check if the socket is connected or not.

        Returns:
            bool. True if connection was already made, False otherwise.
        """
        return self.token is not None

    def disconnect(self):
        """Cleanup the client."""
        self.token = None
        self.websocket.close()

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

    def get_statistics(self, test_name,
                       max_sample_size=None,
                       min_duration_cut=None,
                       max_iterations=None,
                       acceptable_ratio=None):
        """Request test duration statistics.

        Args:
            test_name (str): name of the test to search,
                e.g. "MyTest.test_method".
            max_sample_size (number): maximal number of tests to collect.
            min_duration_cut (number): ignore tests under the given duration.
            max_iterations (number): max anomalies removal iterations.
            acceptable_ratio (number): acceptable ration between max and min
                values, under which don't try to remove anomalies.

        Returns:
            dict. dictionary containing the min, max and avg test durations.
        """
        request_data = StatisticsRequestModel({
            "test_name": test_name,
            "max_sample_size": max_sample_size,
            "min_duration_cut": min_duration_cut,
            "max_iterations": max_iterations,
            "acceptable_ratio": acceptable_ratio})

        response = self.requester.request(GetTestStatistics,
                                          data=request_data,
                                          method="get")

        if isinstance(response, FailureResponseModel):
            raise RuntimeError(response.details)

        return response.body
