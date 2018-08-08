import httplib

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rotest.api.constants import \
    RESPONSE_PAGE_NOT_IMPLEMENTED


@csrf_exempt
def add_test_result(request, sessions=None, *args, **kwargs):
    """Add a result to the test.

    Args:
        test_id (number): the identifier of the test.
        result_code (number): code of the result as defined in TestOutcome.
        info (str): additional info (traceback / end reason etc).
    """
    if request.method != "POST":
        return JsonResponse(RESPONSE_PAGE_NOT_IMPLEMENTED,
                            status=httplib.BAD_REQUEST)

    session_token = request.POST.get("token")
    session_data = sessions[session_token]
    test_data = session_data.all_tests[request.POST.get("test_id")]
    test_data.update_result(request.POST.get("result_code"),
                            request.POST.get("info"))
    test_data.save()

    return JsonResponse({}, status=httplib.NO_CONTENT)
