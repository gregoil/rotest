from swaggapi.api.builder.common.fields import (StringField,
                                               ModelField,
                                               ArrayField)
from swaggapi.api.builder.common.response import AbstractResponse

from rotest.api.common import EmptyModel


class EmptyResponse(AbstractResponse):
    PROPERTIES = []


class TokenResponseModel(AbstractResponse):
    """Token Response."""
    TITLE = "Token Response"
    PROPERTIES = [
        StringField(name="token", description="Token of the current session")
    ]


class DetailedResponseModel(AbstractResponse):
    "Details about the executed request"
    PROPERTIES = [
        StringField(name="details", required=True)
    ]


class BadRequestResponseModel(AbstractResponse):
    "Invalid request given"
    PROPERTIES = [
        StringField(name="details", required=True),
        ModelField(name="errors", model=EmptyModel)
    ]


class InfluencedResourcesResponseModel(AbstractResponse):
    "Returns an array of influenced Resources."
    PROPERTIES = [
        ArrayField(name="resource_descriptors", items_type=EmptyModel,
                   required=True)
    ]

