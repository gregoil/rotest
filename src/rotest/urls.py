from django.conf.urls import include, url, patterns

urlpatterns = patterns("",
    url("^api/?", include("rotest.api.urls")),
)
