# pylint: disable=unused-argument, no-self-use
from __future__ import absolute_import

from six.moves import http_client
from django.db import transaction
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.api.common.responses import SuccessResponse
from rotest.management.common.utils import extract_type
from rotest.api.common.models import UpdateFieldsParamsModel


class UpdateFields(DjangoRequestView):
    """Update content in the server's DB.

    Args:
        model (str): Django model to apply changes on.
        filter (dict): arguments to filter by.
        kwargs_vars (dict): the additional arguments are the changes to
            apply on the filtered instances.
    """
    URI = "resources/update_fields"
    DEFAULT_MODEL = UpdateFieldsParamsModel
    DEFAULT_RESPONSES = {
        http_client.NO_CONTENT: SuccessResponse,
    }
    TAGS = {
        "put": ["Resources"]
    }

    def put(self, request, *args, **kwargs):
        """Update content in the server's DB.

        Args:
            model (type): Django model to apply changes on.
            filter (dict): arguments to filter by.
            changes (dict): the additional arguments are the changes to
                apply on the filtered instances.
        """
        model = extract_type(request.model.resource_descriptor.type)
        filter_dict = request.model.resource_descriptor.properties
        kwargs_vars = request.model.changes
        with transaction.atomic():
            objects = model.objects.select_for_update()
            if filter_dict is not None and len(filter_dict) > 0:
                objects.filter(**filter_dict).update(**kwargs_vars)

            else:
                objects.all().update(**kwargs_vars)

        return Response({}, status=http_client.NO_CONTENT)
