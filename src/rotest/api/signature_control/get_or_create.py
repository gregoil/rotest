# pylint: disable=unused-argument
from __future__ import absolute_import

import re

from six.moves import http_client

from rotest.core.models import SignatureData
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.api.common.responses import SignatureResponse
from rotest.api.common.models import SignatureControlParamsModel


class GetOrCreate(DjangoRequestView):
    """Get or create error signature in the DB.

    Args:
        error_string (str): string of the error.
    """
    URI = "signatures/get_or_create"
    DEFAULT_MODEL = SignatureControlParamsModel
    DEFAULT_RESPONSES = {
        http_client.OK: SignatureResponse,
    }
    TAGS = {
        "get": ["Signatures"]
    }

    signatures_cache = None

    def _match_signatures(self, error_str):
        """Return the data of the matched signature.

        Args:
            error_str (str): exception traceback string.

        Returns:
            SignatureData. the signature of the given exception.
        """
        for signature in self.signatures_cache:
            signature_reg = re.compile(signature.pattern,
                                       re.DOTALL | re.MULTILINE)
            if signature_reg.match(error_str):
                return signature

        return None

    def get(self, request, *args, **kwargs):
        """Get signature data for an error or create a new one."""
        error_message = request.model.error

        if self.signatures_cache is None:
            self.signatures_cache = list(SignatureData.objects.all())

        match = self._match_signatures(error_message)

        is_new = False
        if match is None:
            # Create a new signature
            is_new = True
            pattern = SignatureData.create_pattern(error_message)
            match = SignatureData.objects.create(link="",
                                                 pattern=pattern)

            # Add to cache
            self.signatures_cache.append(match)

        return Response({
            "is_new": is_new,
            "id": match.id,
            "link": match.link
        }, status=http_client.OK)
