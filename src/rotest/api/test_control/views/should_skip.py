import httplib

from django.http import JsonResponse

from rotest.api.constants import \
    RESPONSE_PAGE_NOT_IMPLEMENTED


SKIP_DELTA_MESSAGE = "Previous run passed according to remote DB"


def should_skip(request, sessions=None, *args, **kwargs):
    """Check if the test passed in the last run according to results DB.

    Args:
        test_id (number): the identifier of the test.
    """
    if request.method != "GET":
        return JsonResponse(RESPONSE_PAGE_NOT_IMPLEMENTED,
                            status=httplib.BAD_REQUEST)

    session_token = request.GET.get("token")
    session_data = sessions[session_token]
    test_data = session_data.all_tests[request.GET.get("test_id")]
    run_data = session_data.run_data

    test_should_skip = test_data.should_skip(test_name=test_data.name,
                                             run_data=run_data,
                                             exclude_pk=test_data.pk)
    reason = SKIP_DELTA_MESSAGE if test_should_skip else ""

    return JsonResponse({
        "should_skip": test_should_skip,
        "reason": reason
    }, status=httplib.OK)
