# pylint: disable=unused-argument, no-self-use
from __future__ import absolute_import

from six.moves import http_client
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.exceptions import BadRequest
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.api.test_control.middleware import session_middleware
from rotest.api.common.models import TestControlOperationParamsModel
from rotest.api.common.responses import SuccessResponse, FailureResponseModel


class StopTest(DjangoRequestView):
    """End a test run.

    Args:
        test_id (number): the identifier of the test.
        token (str): token of the session.
    """
    URI = "tests/stop_test"
    DEFAULT_MODEL = TestControlOperationParamsModel
    DEFAULT_RESPONSES = {
        http_client.NO_CONTENT: SuccessResponse,
        http_client.BAD_REQUEST: FailureResponseModel
    }
    TAGS = {
        "post": ["Tests"]
    }

    @session_middleware
    def post(self, request, sessions, *args, **kwargs):
        """End a test run.

        Args:
            request (Request): StopTest request.
        """
        session_token = request.model.token
        try:
            session_data = sessions[session_token]
            test_data = session_data.all_tests[request.model.test_id]

        except KeyError:
            raise BadRequest("Invalid token/test_id provided!")

        test_data.end()
        test_data.save()

        return Response({}, status=http_client.NO_CONTENT)
