import httplib

from django.http import JsonResponse
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.api.common.responses import EmptyResponse
from rotest.api.common.models import AddTestResultModel
from rotest.api.test_control.middleware import session_middleware


# pylint: disable=unused-argument, no-self-use


class AddTestResult(DjangoRequestView):
    """Add a result to the test.

    Args:
        test_id (number): the identifier of the test.
        result_code (number): code of the result as defined in TestOutcome.
        info (str): additional info (traceback / end reason etc).
    """
    URI = "tests/add_test_result"
    DEFAULT_MODEL = AddTestResultModel
    DEFAULT_RESPONSES = {
        httplib.NO_CONTENT: EmptyResponse,
    }
    TAGS = {
        "post": ["Tests"]
    }

    @session_middleware
    def post(self, request, sessions, *args, **kwargs):
        """Add a result to the test.

        Args:
            test_id (number): the identifier of the test.
            result_code (number): code of the result as defined in TestOutcome.
            info (str): additional info (traceback / end reason etc).
        """
        session_token = request.model.test_details.token
        session_data = sessions[session_token]
        test_data = session_data.all_tests[request.model.test_details.test_id]
        test_data.update_result(request.model.result.result_code,
                                request.model.result.info)
        test_data.save()

        return JsonResponse({}, status=httplib.NO_CONTENT)
