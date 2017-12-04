"""Django definitions for the administrator site urls."""
import django
from django.contrib import admin
from django.conf.urls import patterns, include, url


django.setup()
admin.autodiscover()
urlpatterns = patterns('', url(r'^admin/', include(admin.site.urls)))
