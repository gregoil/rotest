from django.conf.urls import include, url, patterns

urlpatterns = patterns("",
    url("^tests/?", include("rotest.api.test_control.urls")),
    url("^resources/?", include("rotest.api.resource_control.urls")),
)