"""Django definitions for the administrator site urls."""
from rotest.frontend import views
from django.contrib import admin
from django.conf.urls import include, url

urlpatterns = [
    url(r'^$', "rotest.frontend.views.index"),
]
