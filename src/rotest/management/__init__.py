from django.apps import AppConfig


class ManagementConfig(AppConfig):
    name = "rotest.management"

    def ready(self):
        from .models import ResourceData
        from .client.manager import ClientResourceManager
        from .base_resource import BaseResource, ResourceRequest

        from rotest import management
        management.ResourceData = ResourceData
        management.ClientResourceManager = ClientResourceManager
        management.BaseResource = BaseResource
        management.ResourceRequest = ResourceRequest


default_app_config = "rotest.management.ManagementConfig"
