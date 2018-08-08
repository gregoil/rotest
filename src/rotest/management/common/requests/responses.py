from rotest.management.common.requests.base_api import AbstractAPIModel
from rotest.management.common.requests.fields import TokenField


class TokenResponseModel(AbstractAPIModel):
    """Token Response"""
    TITLE = "Token Response"
    PROPERTIES = [
        TokenField
    ]

