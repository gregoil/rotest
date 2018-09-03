"""Django definitions for the administrator site urls."""
from django.contrib import admin
from django.conf.urls import include, url

admin.autodiscover()
urlpatterns = [
    url(r'^rotest/api/', include("rotest.api.urls")),
    url(r'^admin/', include(admin.site.urls)),
]
