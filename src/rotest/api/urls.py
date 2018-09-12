"""URLs of all the django views."""
# pylint: disable=unused-argument, no-self-use
from django.conf.urls import patterns

from swaggapi.build import Swagger
from swaggapi.api.openapi.models import Info, License, Tag

from rotest.api.request_token import RequestToken
from rotest.api.resource_control import (CleanupUser,
                                         LockResources,
                                         ReleaseResources,
                                         QueryResources,
                                         UpdateFields)
from rotest.api.test_control import (StartTestRun,
                                     UpdateRunData,
                                     StopTest,
                                     StartTest,
                                     StopComposite,
                                     StartComposite,
                                     ShouldSkip,
                                     AddTestResult, UpdateResources)

requests = [
    RequestToken,

    # resources
    LockResources,
    ReleaseResources,
    CleanupUser,
    QueryResources,
    UpdateFields,

    # tests
    StartTestRun,
    UpdateRunData,
    StopTest,
    StartTest,
    StopComposite,
    StartComposite,
    ShouldSkip,
    AddTestResult,
    UpdateResources
]

info = Info(title="Rotest OpenAPI",
            version="0.1.0",
            description="Rotest Swagger for resource and test management",
            license=License(name="MIT"))
tags = [Tag(name="Tests",
            description="All requests for managing remote test handler"),
        Tag(name="Resources",
            description="All requests for managing resources")]
swagger = Swagger(info, mount_url="api", requests=requests, tags=tags)


urlpatterns = patterns("", *swagger.get_django_urls())
