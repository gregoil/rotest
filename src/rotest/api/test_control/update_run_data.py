# pylint: disable=unused-argument, no-self-use
import httplib

from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.core.models import RunData
from rotest.api.common.responses import SuccessResponse
from rotest.api.common.models import UpdateRunDataModel
from rotest.api.test_control.middleware import session_middleware


class UpdateRunData(DjangoRequestView):
    """Initialize the tests run data.

    Args:
        token (str): token of the session.
        run_data (dict): properties of run data to update.
    """
    URI = "tests/update_run_data"
    DEFAULT_MODEL = UpdateRunDataModel
    DEFAULT_RESPONSES = {
        httplib.NO_CONTENT: SuccessResponse,
    }
    TAGS = {
        "post": ["Tests"]
    }

    @session_middleware
    def post(self, request, sessions, *args, **kwargs):
        """Initialize the tests run data."""
        session_token = request.model.token
        session_data = sessions[session_token]
        run_data = session_data.run_data
        RunData.objects.filter(pk=run_data.pk).update(
            **request.model.run_data)

        return Response({}, status=httplib.NO_CONTENT)
