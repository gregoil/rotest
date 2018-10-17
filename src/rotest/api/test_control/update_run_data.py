# pylint: disable=unused-argument, no-self-use
from __future__ import absolute_import

from six.moves import http_client
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.exceptions import BadRequest
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.core.models import RunData
from rotest.api.common.models import UpdateRunDataParamsModel
from rotest.api.test_control.middleware import session_middleware
from rotest.api.common.responses import SuccessResponse, FailureResponseModel


class UpdateRunData(DjangoRequestView):
    """Initialize the tests run data.

    Args:
        token (str): token of the session.
        run_data (dict): properties of run data to update.
    """
    URI = "tests/update_run_data"
    DEFAULT_MODEL = UpdateRunDataParamsModel
    DEFAULT_RESPONSES = {
        http_client.NO_CONTENT: SuccessResponse,
        http_client.BAD_REQUEST: FailureResponseModel
    }
    TAGS = {
        "post": ["Tests"]
    }

    @session_middleware
    def post(self, request, sessions, *args, **kwargs):
        """Initialize the tests run data."""
        session_token = request.model.token
        try:
            session_data = sessions[session_token]

        except KeyError:
            raise BadRequest("Invalid token provided!")

        run_data = session_data.run_data
        RunData.objects.filter(pk=run_data.pk).update(
            **request.model.run_data)

        return Response({}, status=http_client.NO_CONTENT)
