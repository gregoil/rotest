from django.conf.urls import url, patterns

from rotest.api.resource_control.views.cleanup_user import cleanup_user
from rotest.api.resource_control.views.lock_resources import lock_resources
from rotest.api.resource_control.views.query_resources import query_resources
from rotest.api.resource_control.views.release_resources import \
    release_resources
from rotest.api.resource_control.views.update_fields import update_fields

urlpatterns = patterns("",
    url("^lock_resources/?", lock_resources),
    url("^release_resources/?", release_resources),
    url("^query_resources/?", query_resources),
    url("^cleanup_user/?", cleanup_user),
    url("^update_fields/?", update_fields),
)
