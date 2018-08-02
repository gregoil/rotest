from django.conf.urls import include, url
from rotest.api import test_control, resource_control

urlpatterns = [
    url("^tests/?", include(test_control.urls)),
    url("^resources/?", include(resource_control.urls)),
]