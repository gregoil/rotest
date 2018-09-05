# pylint: disable=unused-argument, no-self-use
import uuid
import httplib

from swaggapi.api.builder.server.exceptions import BadRequest
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.core.models import RunData
from rotest.api.common.models import GenericModel
from rotest.management.common.json_parser import JSONParser
from rotest.api.test_control.middleware import session_middleware, SessionData
from rotest.api.common.responses import (TokenResponseModel,
                                         FailureResponseModel)


TEST_ID_KEY = 'id'
TEST_NAME_KEY = 'name'
TEST_CLASS_CODE_KEY = 'class'
TEST_SUBTESTS_KEY = 'subtests'


class RequestToken(DjangoRequestView):
    """Initialize the tests run data.

    Args:
        tests_tree (dict): contains the hierarchy of the tests in the run.
        run_data (dict): contains additional data about the run.
    """
    URI = "tests/get_token"
    DEFAULT_MODEL = GenericModel
    DEFAULT_RESPONSES = {
        httplib.OK: TokenResponseModel,
        httplib.BAD_REQUEST: FailureResponseModel
    }
    TAGS = {
        "get": ["Token"]
    }

    @session_middleware
    def post(self, request, sessions, *args, **kwargs):
        """Initialize the tests run data.

        Args:
            tests_tree (dict): contains the hierarchy of the tests in the run.
            run_data (dict): contains additional data about the run.
        """
        session_token = str(uuid.uuid4())
        sessions[session_token] = SessionData(all_tests=None,
                                              run_data=None,
                                              main_test=None)
        response = {
            "token": session_token
        }
        return Response(response, status=httplib.OK)
