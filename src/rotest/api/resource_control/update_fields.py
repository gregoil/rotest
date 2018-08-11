import httplib

from django.http import JsonResponse
from swagapi.api.wrapper import RequestView

from rotest.api.common.models import (ChangeResourcePostModel)
from rotest.api.common.responses import (BadRequestResponseModel,
                                         EmptyResponse)
from rotest.management.common.utils import extract_type


class UpdateFields(RequestView):
    """Update content in the server's DB.

    Args:
        model (str): Django model to apply changes on.
        filter (dict): arguments to filter by.
        kwargs_vars (dict): the additional arguments are the changes to apply on
            the filtered instances.
    """
    URI = "resources/update_fields"
    DEFAULT_MODEL = ChangeResourcePostModel
    DEFAULT_RESPONSES = {
        httplib.NO_CONTENT: EmptyResponse,
        httplib.BAD_REQUEST: BadRequestResponseModel
    }
    TAGS = {
        "post": ["Resources"]
    }

    def post(self, request, *args, **kwargs):
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
        objects = model.objects
        if filter_dict is not None and len(filter_dict) > 0:
            objects.filter(**filter_dict).update(**kwargs_vars)

        else:
            objects.all().update(**kwargs_vars)

        return JsonResponse({}, status=httplib.NO_CONTENT)
