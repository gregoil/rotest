"""URLs of all the django views."""
# pylint: disable=unused-argument, no-self-use
from __future__ import absolute_import
from django.conf.urls import patterns

from swaggapi.build import Swagger
from swaggapi.api.openapi.models import Info, License, Tag

from rotest.api.request_token import RequestToken
from rotest.api.signature_control import GetOrCreate
from rotest.api.resource_control import (CleanupUser,
                                         LockResources,
                                         ReleaseResources,
                                         QueryResources,
                                         UpdateFields)
from rotest.api.test_control import (StartTestRun,
                                     UpdateRunData,
                                     StopTest,
                                     StartTest,
                                     SetSessionTimeout,
                                     StopComposite,
                                     StartComposite,
                                     ShouldSkip,
                                     AddTestResult,
                                     UpdateResources)

requests = [
    RequestToken,

    # Resources
    LockResources,
    ReleaseResources,
    CleanupUser,
    QueryResources,
    UpdateFields,

    # Tests
    StartTestRun,
    UpdateRunData,
    StopTest,
    StartTest,
    SetSessionTimeout,
    StopComposite,
    StartComposite,
    ShouldSkip,
    AddTestResult,
    UpdateResources,

    # Signatures
    GetOrCreate
]

info = Info(title="Rotest OpenAPI",
            version="0.1.0",
            description="Rotest Swagger for resource and test management",
            license=License(name="MIT"))
tags = [Tag(name="Tests",
            description="All requests for managing remote test handler"),
        Tag(name="Signatures",
            description="All requests for managing signatures handler"),
        Tag(name="Resources",
            description="All requests for managing resources")]
swagger = Swagger(info, mount_url="api", requests=requests, tags=tags)


urlpatterns = patterns("", *swagger.get_django_urls())
