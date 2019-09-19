"""Django definitions for the administrator site urls."""
from __future__ import absolute_import
from django.contrib import admin
from django.conf.urls import include, url


urlpatterns = [
    url(r'^rotest/api/', include("rotest.api.urls")),
    url(r'^admin/', admin.site.urls),
]
