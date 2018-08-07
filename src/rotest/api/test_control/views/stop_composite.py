import httplib

from django.http import JsonResponse

from rotest.api.constants import \
    RESPONSE_PAGE_NOT_IMPLEMENTED


def stop_composite(request, sessions=None, *args, **kwargs):
    """Save the composite test's data.

    Args:
        test_id (number): the identifier of the test.
    """
    if request.method != "POST":
        return JsonResponse(RESPONSE_PAGE_NOT_IMPLEMENTED,
                            status=httplib.BAD_REQUEST)

    session_token = request.POST.get("token")
    session_data = sessions[session_token]
    test_data = session_data.all_tests[request.POST.get("test_id")]
    has_succeeded = all(sub_test.success for sub_test in test_data)
    test_data.success = has_succeeded
    test_data.end()
    test_data.save()

    return JsonResponse({}, status=httplib.NO_CONTENT)
