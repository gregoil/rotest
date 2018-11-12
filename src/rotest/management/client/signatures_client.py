"""Signature manager client implementation."""
from __future__ import absolute_import

from rotest.common import core_log
from rotest.api.signature_control import GetOrCreate
from rotest.common.config import RESOURCE_MANAGER_HOST
from rotest.management.client.client import AbstractClient
from rotest.api.common.responses import FailureResponseModel
from rotest.api.common.models import SignatureControlParamsModel


class ClientSignatureManager(AbstractClient):
    """Client side signature manager.

    Responsible for updating and querying the server of signature data.
    """

    def __init__(self, host=None, logger=core_log):
        if host is None:
            host = RESOURCE_MANAGER_HOST

        super(ClientSignatureManager, self).__init__(logger=logger, host=host)

    def get_or_create_signature(self, error_string):
        """Get or create an error signature in the remote db.

        Args:
            error_string (str): string of the error.

        Returns:
            SignatureResponse. response containing signature data.
        """
        request_data = SignatureControlParamsModel({
            "error": error_string
        })

        response = self.requester.request(GetOrCreate,
                                          data=request_data,
                                          method="post")

        if isinstance(response, FailureResponseModel):
            raise RuntimeError(response.details)

        return response
