from django.conf.urls import include, url
from rotest import api

urlpatterns = [
    url("^api/?", include(api.urls)),
]