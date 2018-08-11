import httplib

from swagapi.api.wrapper import RequestView, Response

from rotest.api.common.responses import (BadRequestResponseModel,
                                         DetailedResponseModel)
from rotest.management import ResourceData
from rotest.management.common.utils import get_username


class CleanupUser(RequestView):
    """Cleaning up user's requests and locked resources."""
    URI = "resources/cleanup_user"
    DEFAULT_RESPONSES =  {
        httplib.OK: DetailedResponseModel,
        httplib.BAD_REQUEST: BadRequestResponseModel
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
        resources = ResourceData.objects.filter(owner=user_name)
        if resources.count() == 0:
            return Response({
                "details": "User {} didn't lock any resource".format(user_name)
            }, status=httplib.OK)

        else:
            resources.update(owner="", owner_time=None)
            return Response({
                "details": "User {} was successfully cleaned".format(user_name)
            }, status=httplib.OK)
