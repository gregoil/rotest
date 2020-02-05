"""Rotest management application."""
# pylint: disable=redefined-outer-name
from django.apps import AppConfig


class ManagementConfig(AppConfig):
    name = "rotest.management"

    def ready(self):
        from .models import ResourceData
        from .models.resource_data import DataPointer
        from .client.manager import ClientResourceManager
        from .base_resource import BaseResource, ResourceRequest

        import rotest
        rotest.management.ResourceData = ResourceData
        rotest.management.ClientResourceManager = ClientResourceManager
        rotest.management.BaseResource = BaseResource
        rotest.management.ResourceRequest = ResourceRequest
        rotest.management.DataPointer = DataPointer


default_app_config = "rotest.management.ManagementConfig"
