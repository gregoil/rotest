import httplib

from rotest.management.common.requests.base_api import AbstractRequest
from rotest.management.common.requests.fields import (DescriptorsField,
                                                      ResourcesField)
from rotest.management.common.requests.responses import (TokenResponseModel)


class LockResources(AbstractRequest):
    """Lock the given resources one by one"""
    URI = "resources/lock_resources"
    METHOD = "POST"
    TAGS = ["Resources"]
    PARAMS = [
        DescriptorsField
    ]
    RESPONSES = {
        httplib.OK: TokenResponseModel
    }


class ReleaseResources(AbstractRequest):
    """Release the given resources one by one"""
    URI = "resources/release_resources"
    METHOD = "POST"
    TAGS = ["Resources"]
    PARAMS = [
        ResourcesField
    ]


class UpdateFields(AbstractRequest):
    """Update content in the server's DB"""
    URI = "resources/update_fields"
    METHOD = "POST"
    TAGS = ["Resources"]
    PARAMS = [

    ]


class CleanupUser(AbstractRequest):
    """Cleaning up user's requests and locked resources"""
    URI = "resources/cleanup_user"
    METHOD = "POST"
    TAGS = ["Resources"]
    PARAMS = [

    ]


class QueryResources(AbstractRequest):
    """Find and return the resources that answer the client's query"""
    URI = "resources/query_resources"
    METHOD = "GET"
    TAGS = ["Resources"]
    PARAMS = [

    ]
