from django.conf.urls import include, url, patterns

from rotest.api.swagger.index import swagger_file, index

urlpatterns = patterns("",
    url("^tests/?", include("rotest.api.test_control.urls")),
    url("^resources/?", include("rotest.api.resource_control.urls")),
    url("^swagger/?$", index),
    url("^swagger/swagger.json$", swagger_file),
)
