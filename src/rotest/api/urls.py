import httplib

from django.shortcuts import render
from django.http import JsonResponse
from django.conf.urls import patterns, url

from swaggapi.build import Swagger
from swaggapi.api.openapi.models import (Info, License, Tag)

from rotest.api.resource_control import (CleanupUser,
                                         LockResources,
                                         ReleaseResources,
                                         QueryResources,
                                         UpdateFields)


# pylint: disable=unused-argument, no-self-use


requests = [LockResources,
            ReleaseResources,
            CleanupUser,
            QueryResources,
            UpdateFields]

info = Info(title="Rotest OpenAPI",
            version="0.1.0",
            description="Rotest Swagger for resource and test management",
            license=License(name="MIT"))
tags = [Tag(name="Tests",
            description="All requests for managing remote test handler"),
        Tag(name="Resources",
            description="All requests for managing resources")]
swagger = Swagger(info, mount_url="api", requests=requests, tags=tags)


def swagger_file(request, *args, **kwargs):
    swagger.configure_base_url(request)
    return JsonResponse(swagger.api.json(), status=httplib.OK)


def index(request, *args, **kwargs):
    return render(request, "swagger.html")


urlpatterns = patterns("",
    url("^$", index),
    url("^swagger.json$", swagger_file),
    *swagger.get_django_urls()
)
