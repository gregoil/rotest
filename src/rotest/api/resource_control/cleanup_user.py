# pylint: disable=unused-argument, no-self-use
import httplib

from django.db import transaction
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.management import ResourceData
from rotest.api.common.responses import SuccessResponse
from rotest.management.common.utils import get_username


class CleanupUser(DjangoRequestView):
    """Cleaning up user's requests and locked resources."""
    URI = "resources/cleanup_user"
    DEFAULT_RESPONSES = {
        httplib.NO_CONTENT: SuccessResponse,
    }
    TAGS = {
        "post": ["Resources"]
    }

    def post(self, request, *args, **kwargs):
        """Clean up user's requests and locked resources.

        Args:
            username (str): the username to cleanup.

        Returns:
            SuccessReply. a reply indicating on a successful operation.
        """
        username = get_username(request)
        with transaction.atomic():
            resources = ResourceData.objects.select_for_update().filter(
                owner=username)

            resources.update(owner="", owner_time=None)

        return Response({
            "details": "User {} was successfully cleaned".format(username)
        }, status=httplib.NO_CONTENT)
