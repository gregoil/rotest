"""Responses models of the view requests."""
from swaggapi.api.builder.common.response import AbstractResponse
from swaggapi.api.builder.common.fields import (StringField,
                                                ModelField,
                                                ArrayField, BoolField)

from rotest.api.common import GenericModel


class SuccessResponse(AbstractResponse):
    """Returns when request ended successfully - with no content."""
    PROPERTIES = []


class TokenResponseModel(AbstractResponse):
    """Returns a token of the created sessions."""
    TITLE = "Token Response"
    PROPERTIES = [
        StringField(name="token", description="Token of the current session",
                    required=True)
    ]


class FailureResponseModel(AbstractResponse):
    """Returns when an invalid request is received."""
    PROPERTIES = [
        StringField(name="details", required=True),
        ModelField(name="errors", model=GenericModel)
    ]


class InfluencedResourcesResponseModel(AbstractResponse):
    """Returns an array of the resources influenced by the action."""
    PROPERTIES = [
        ArrayField(name="resource_descriptors", items_type=GenericModel,
                   required=True)
    ]


class ShouldSkipResponse(AbstractResponse):
    """Returns if the test should be skip and the reason why."""
    PROPERTIES = [
        BoolField(name="should_skip", required=True),
        StringField(name="reason", required=True)
    ]
