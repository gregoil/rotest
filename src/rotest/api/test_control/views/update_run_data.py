import httplib

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rotest.core.models import RunData
from rotest.api.constants import \
    RESPONSE_PAGE_NOT_IMPLEMENTED


# pylint: disable=unused-argument, no-self-use


@csrf_exempt
def update_run_data(request, sessions=None, *args, **kwargs):
    """Initialize the tests run data.

    Args:
        run_data (dict): containts additional data about the run.
    """
    if request.method != "POST":
        return JsonResponse(RESPONSE_PAGE_NOT_IMPLEMENTED,
                            status=httplib.BAD_REQUEST)

    session_token = request.POST.get("token")
    session_data = sessions[session_token]
    run_data = session_data.run_data
    RunData.objects.filter(pk=run_data.pk).update(**run_data)

    return JsonResponse({}, status=httplib.NO_CONTENT)
