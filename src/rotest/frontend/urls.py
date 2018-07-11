"""Django definitions for the administrator site urls."""
from rotest.frontend import views
from django.contrib import admin
from django.conf.urls import include, url

import utils

urlpatterns = [
    url(r'^rotest/api/release_owner/(?P<data_name>.*?)/?$',
        utils.set_field("owner"), name="remove_resource_owner"),
    url(r'^rotest/api/release_reserved/(?P<data_name>.*?)/?$',
            utils.set_field("reserved"), name="remove_resource_reserved"),
    url(r'^rotest/api/lock_resource/(?P<data_name>.*?)/?$',
            utils.lock_resource, name="lock_resource"),
    url(r'^/?', "rotest.frontend.views.index"),
]
