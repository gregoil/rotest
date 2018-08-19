# pylint: disable=unused-argument, no-self-use
import httplib

from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.api.common.models import TestOperation
from rotest.api.common.responses import ShouldSkipResponse
from rotest.api.test_control.middleware import session_middleware


SKIP_DELTA_MESSAGE = "Previous run passed according to remote DB"


class ShouldSkip(DjangoRequestView):
    """Check if the test passed in the last run according to results DB.

    Args:
        test_id (number): the identifier of the test.
        token (str): token of the session.
    """
    URI = "tests/should_skip"
    DEFAULT_MODEL = TestOperation
    DEFAULT_RESPONSES = {
        httplib.OK: ShouldSkipResponse,
    }
    TAGS = {
        "post": ["Tests"]
    }

    @session_middleware
    def post(self, request, sessions, *args, **kwargs):
        """Check if the test passed in the last run according to results DB.

        Args:
            test_id (number): the identifier of the test.
            token (str): token of the session.
        """
        session_token = request.model.token
        session_data = sessions[session_token]
        test_data = session_data.all_tests[request.model.test_id]
        run_data = session_data.run_data

        test_should_skip = test_data.should_skip(test_name=test_data.name,
                                                 run_data=run_data,
                                                 exclude_pk=test_data.pk)
        reason = SKIP_DELTA_MESSAGE if test_should_skip else ""

        return Response({
            "should_skip": test_should_skip,
            "reason": reason
        }, status=httplib.OK)
