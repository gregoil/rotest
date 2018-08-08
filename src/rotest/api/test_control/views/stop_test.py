import httplib

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rotest.api.constants import \
    RESPONSE_PAGE_NOT_IMPLEMENTED


@csrf_exempt
def stop_test(request, sessions=None, *args, **kwargs):
    """End a test run.

    Args:
        request (Request): StopTest request.
    """
    if request.method != "POST":
        return JsonResponse(RESPONSE_PAGE_NOT_IMPLEMENTED,
                            status=httplib.BAD_REQUEST)

    session_token = request.POST.get("token")
    session_data = sessions[session_token]
    test_data = session_data.all_tests[request.POST.get("test_id")]
    test_data.end()
    test_data.save()

    return JsonResponse({}, status=httplib.NO_CONTENT)
