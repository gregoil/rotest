# pylint: disable=unused-argument,no-self-use
from __future__ import absolute_import

from six.moves import http_client
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.exceptions import BadRequest
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.api.test_control.middleware import session_middleware
from rotest.api.common.models import TestControlOperationParamsModel
from rotest.api.common.responses import (ShouldSkipResponse,
                                         FailureResponseModel)


SKIP_DELTA_MESSAGE = "Previous run passed according to remote DB"


class ShouldSkip(DjangoRequestView):
    """Check if the test passed in the last run according to results DB.

    Args:
        test_id (number): the identifier of the test.
        token (str): token of the session.
    """
    URI = "tests/should_skip"
    DEFAULT_MODEL = TestControlOperationParamsModel
    DEFAULT_RESPONSES = {
        http_client.OK: ShouldSkipResponse,
        http_client.BAD_REQUEST: FailureResponseModel
    }
    TAGS = {
        "get": ["Tests"]
    }

    @session_middleware
    def get(self, request, sessions, *args, **kwargs):
        """Check if the test passed in the last run according to results DB.

        Args:
            test_id (number): the identifier of the test.
            token (str): token of the session.
        """
        session_token = request.model.token
        try:
            session_data = sessions[session_token]
            test_data = session_data.all_tests[request.model.test_id]

        except KeyError:
            raise BadRequest("Invalid token/test_id provided!")

        run_data = session_data.run_data

        test_should_skip = test_data.should_skip(test_name=test_data.name,
                                                 run_data=run_data,
                                                 exclude_pk=test_data.pk)
        reason = SKIP_DELTA_MESSAGE if test_should_skip else ""

        return Response({
            "should_skip": test_should_skip,
            "reason": reason
        }, status=http_client.OK)
