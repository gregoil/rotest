import httplib

from django.db import transaction
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.management import ResourceData
from rotest.management.common.utils import get_username
from rotest.api.common.responses import DetailedResponseModel


# pylint: disable=unused-argument, no-self-use


class CleanupUser(DjangoRequestView):
    """Cleaning up user's requests and locked resources."""
    URI = "resources/cleanup_user"
    DEFAULT_RESPONSES = {
        httplib.OK: DetailedResponseModel,
    }
    TAGS = {
        "post": ["Resources"]
    }

    def post(self, request, *args, **kwargs):
        """Cleaning up user's requests and locked resources.

        Args:
            username (str): the username to cleanup.

        Returns:
            SuccessReply. a reply indicating on a successful operation.
        """
        user_name = get_username(request)
        with transaction.atomic():
            resources = ResourceData.objects.select_for_update().filter(
                owner=user_name)

            if resources.count() == 0:
                return Response({
                    "details": "User {} didn't lock any resource".format(
                        user_name)
                }, status=httplib.OK)

            resources.update(owner="", owner_time=None)
        return Response({
            "details": "User {} was successfully cleaned".format(user_name)
        }, status=httplib.OK)
