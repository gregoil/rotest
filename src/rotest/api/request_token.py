# pylint: disable=unused-argument, no-self-use
from __future__ import absolute_import

import uuid

from future.builtins import str
from six.moves import http_client
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.api.common.models import GenericModel
from rotest.api.test_control.middleware import session_middleware, SessionData
from rotest.api.common.responses import (TokenResponseModel,
                                         FailureResponseModel)


class RequestToken(DjangoRequestView):
    """Create a session for the client and return its unique token."""
    URI = "tests/get_token"
    DEFAULT_MODEL = GenericModel
    DEFAULT_RESPONSES = {
        http_client.OK: TokenResponseModel,
        http_client.BAD_REQUEST: FailureResponseModel
    }
    TAGS = {
        "get": ["Token"]
    }

    @session_middleware
    def get(self, request, sessions, *args, **kwargs):
        """Create a session for the client and return its unique token."""
        session_token = str(uuid.uuid4())
        sessions[session_token] = SessionData()
        response = {
            "token": session_token
        }
        return Response(response, status=http_client.OK)
