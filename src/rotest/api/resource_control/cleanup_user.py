# pylint: disable=unused-argument, no-self-use
from __future__ import absolute_import

from six.moves import http_client
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.api.common.models import TokenModel
from rotest.api.common.responses import SuccessResponse
from rotest.management.common.utils import get_username
from rotest.api.test_control.middleware import session_middleware
from rotest.api.resource_control.release_resources import ReleaseResources


class CleanupUser(DjangoRequestView):
    """Cleaning up user's requests and locked resources."""
    URI = "resources/cleanup_user"
    DEFAULT_MODEL = TokenModel
    DEFAULT_RESPONSES = {
        http_client.NO_CONTENT: SuccessResponse,
    }
    TAGS = {
        "post": ["Resources"]
    }

    @session_middleware
    def post(self, request, sessions, *args, **kwargs):
        """Clean up user's requests and locked resources.

        Args:
            username (str): the username to cleanup.

        Returns:
            SuccessReply. a reply indicating on a successful operation.
        """
        username = get_username(request)
        session = sessions[request.model.token]
        for resource in session.resources:
            ReleaseResources.release_resource(resource, username=None)

        return Response({
            "details": "User {} was successfully cleaned".format(username)
        }, status=http_client.NO_CONTENT)
