# pylint: disable=unused-argument, no-self-use
from __future__ import absolute_import

from six.moves import http_client
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.exceptions import BadRequest
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.api.common.models import AddTestResultParamsModel
from rotest.api.test_control.middleware import session_middleware
from rotest.api.common.responses import SuccessResponse, FailureResponseModel


class AddTestResult(DjangoRequestView):
    """Add a result to the test.

    Args:
        test_id (number): the identifier of the test.
        result_code (number): code of the result as defined in TestOutcome.
        info (str): additional info (traceback / end reason etc).
    """
    URI = "tests/add_test_result"
    DEFAULT_MODEL = AddTestResultParamsModel
    DEFAULT_RESPONSES = {
        http_client.NO_CONTENT: SuccessResponse,
        http_client.BAD_REQUEST: FailureResponseModel
    }
    TAGS = {
        "post": ["Tests"]
    }

    @session_middleware
    def post(self, request, sessions, *args, **kwargs):
        """Add a result to the test.

        Args:
            test_id (number): the identifier of the test.
            result_code (number): code of the result as defined in TestOutcome.
            info (str): additional info (traceback / end reason etc).
        """
        session_token = request.model.test_details.token
        try:
            session_data = sessions[session_token]
            test_data = \
                session_data.all_tests[request.model.test_details.test_id]

        except KeyError:
            raise BadRequest("Invalid token/test_id provided!")

        test_data.update_result(request.model.result.result_code,
                                request.model.result.info)
        test_data.save()

        return Response({}, status=http_client.NO_CONTENT)
