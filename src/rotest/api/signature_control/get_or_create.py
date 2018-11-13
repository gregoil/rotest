# pylint: disable=unused-argument
from __future__ import absolute_import

import re

from six.moves import http_client

from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.core.models import SignatureData
from rotest.api.common.responses import SignatureResponse
from rotest.api.common.models import SignatureControlParamsModel


class GetOrCreate(DjangoRequestView):
    """Get or create error signature in the DB.

    Args:
        error (str): string of the error.
    """
    URI = "signatures/get_or_create"
    DEFAULT_MODEL = SignatureControlParamsModel
    DEFAULT_RESPONSES = {
        http_client.OK: SignatureResponse,
    }
    TAGS = {
        "post": ["Signatures"]
    }

    @staticmethod
    def _match_signatures(error_str):
        """Return the data of the matched signature.

        Args:
            error_str (str): exception traceback string.

        Returns:
            SignatureData. the signature of the given exception.
        """
        for signature in SignatureData.objects.all():
            signature_reg = re.compile(signature.pattern,
                                       re.MULTILINE)
            if signature_reg.match(error_str):
                return signature

        return None

    def post(self, request, *args, **kwargs):
        """Get signature data for an error or create a new one."""
        error_message = request.model.error
        # Normalize newline char
        error_message = error_message.replace("\r\n", "\n")

        match = self._match_signatures(error_message)

        is_new = False
        if match is None:
            is_new = True
            pattern = SignatureData.create_pattern(error_message)
            match = SignatureData.objects.create(link="",
                                                 pattern=pattern)

        return Response({
            "is_new": is_new,
            "id": match.id,
            "link": match.link
        }, status=http_client.OK)
