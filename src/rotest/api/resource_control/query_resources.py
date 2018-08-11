import httplib

from django.db import transaction
from django.db.models.query_utils import Q
from django.http import JsonResponse
from swagapi.api.wrapper import RequestView, BadRequest

from rotest.api.common.models import ResourceDescriptorModel
from rotest.api.common.responses import (BadRequestResponseModel,
                                         InfluencedResourcesResponseModel)
from rotest.management.common.json_parser import JSONParser
from rotest.management.common.resource_descriptor import ResourceDescriptor


class QueryResources(RequestView):
    """Find and return the resources that answer the client's query.

    Returns:
        ResourcesReply. a reply containing matching resources.
    """
    URI = "resources/query_resources"
    DEFAULT_MODEL = ResourceDescriptorModel
    DEFAULT_RESPONSES =  {
        httplib.OK: InfluencedResourcesResponseModel,
    }
    TAGS = {
        "post": ["Resources"]
    }

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """Find and return the resources that answer the client's query.

        Args:
            request (Request): QueryResources request.

        Returns:
            ResourcesReply. a reply containing matching resources.
        """
        desc = ResourceDescriptor.decode(request.model.obj)
        # query for resources that are usable and match the descriptors
        query = (Q(is_usable=True, **desc.properties))
        matches = desc.type.objects.filter(query)

        if matches.count() == 0:
            raise BadRequest({
                "details": "No existing resource meets "
                           "the requirements: {!r}".format(desc)
            })

        encoder = JSONParser()
        query_result = [encoder.encode(resource) for resource in matches]

        return JsonResponse({
            "resource_descriptors": query_result
        }, status=httplib.OK)
