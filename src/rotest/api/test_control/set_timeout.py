# pylint: disable=unused-argument, no-self-use
from __future__ import absolute_import

import time

from six.moves import http_client
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.exceptions import BadRequest
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.api.common.models import SetSessionTimeoutModel
from rotest.api.test_control.middleware import session_middleware
from rotest.api.common.responses import SuccessResponse, FailureResponseModel


class SetSessionTimeout(DjangoRequestView):
    """Update the test data to 'in progress' state and set the start time.

    Args:
        timeout (number): the timeout to set.
        token (str): token of the session.
    """
    URI = "tests/set_timeout"
    DEFAULT_MODEL = SetSessionTimeoutModel
    DEFAULT_RESPONSES = {
        http_client.NO_CONTENT: SuccessResponse,
        http_client.BAD_REQUEST: FailureResponseModel
    }
    TAGS = {
        "post": ["Tests"]
    }

    @session_middleware
    def post(self, request, sessions, *args, **kwargs):
        """Update the test data to 'in progress' state and set the start time.

        Args:
            timeout (number): the timeout to set.
        """
        session_token = request.model.token
        try:
            session_data = sessions[session_token]

        except KeyError:
            raise BadRequest("Invalid token provided!")

        session_data.timeout = time.time() + request.model.timeout

        return Response({}, status=http_client.NO_CONTENT)
