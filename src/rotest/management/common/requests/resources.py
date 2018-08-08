from rotest.management.common.requests.base_api import AbstractRequest


class LockResources(AbstractRequest):
    URI = "resources/lock_resources"
    METHOD = "POST"


class ReleaseResources(AbstractRequest):
    URI = "resources/release_resources"
    METHOD = "POST"


class UpdateFields(AbstractRequest):
    URI = "resources/update_fields"
    METHOD = "POST"


class CleanupUser(AbstractRequest):
    URI = "resources/cleanup_user"
    METHOD = "POST"


class QueryResources(AbstractRequest):
    URI = "resources/query_resources"
    METHOD = "POST"

