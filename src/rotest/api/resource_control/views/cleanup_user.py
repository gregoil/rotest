import httplib
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rotest.management import ResourceData
from rotest.api.constants import RESPONSE_PAGE_NOT_IMPLEMENTED
from rotest.management.common.utils import get_username


@csrf_exempt
def cleanup_user(request, *args, **kwargs):
    """Cleaning up user's requests and locked resources.

    Args:
        username (str): the username to cleanup.

    Returns:
        SuccessReply. a reply indicating on a successful operation.
    """
    if request.method != "POST":
        return JsonResponse(RESPONSE_PAGE_NOT_IMPLEMENTED,
                            status=httplib.BAD_REQUEST)

    user_name = get_username(request)
    resources = ResourceData.objects.filter(owner=user_name)
    if resources.count() == 0:
        return JsonResponse({
            "details": "User {} didn't lock any resource".format(user_name)
        }, status=httplib.OK)

    else:
        resources.update(owner="", owner_time=None)
        return JsonResponse({
            "details": "User {} was successfully cleaned".format(user_name)
        }, status=httplib.OK)
