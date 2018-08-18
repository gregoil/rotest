import httplib

from django.db import transaction
from django.db.models.query_utils import Q
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.exceptions import BadRequest
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.management.common.json_parser import JSONParser
from rotest.api.common.models import ResourceDescriptorModel
from rotest.api.common.responses import InfluencedResourcesResponseModel
from rotest.management.common.resource_descriptor import ResourceDescriptor


# pylint: disable=unused-argument, no-self-use


class QueryResources(DjangoRequestView):
    """Find and return the resources that answer the client's query.

    Returns:
        ResourcesReply. a reply containing matching resources.
    """
    URI = "resources/query_resources"
    DEFAULT_MODEL = ResourceDescriptorModel
    DEFAULT_RESPONSES = {
        httplib.OK: InfluencedResourcesResponseModel,
    }
    TAGS = {
        "post": ["Resources"]
    }

    def post(self, request, *args, **kwargs):
        """Find and return the resources that answer the client's query.

        Args:
            request (Request): QueryResources request.

        Returns:
            ResourcesReply. a reply containing matching resources.
        """
        try:
            desc = ResourceDescriptor.decode(request.model.obj)

        except Exception as e:
            raise BadRequest({"details": e.message})

        # query for resources that are usable and match the descriptors
        query = (Q(is_usable=True, **desc.properties))
        query_result = []
        with transaction.atomic():
            matches = desc.type.objects.select_for_update().filter(query)

            if matches.count() == 0:
                raise BadRequest({
                    "details": "No existing resource meets "
                               "the requirements: {!r}".format(desc)
                })

            encoder = JSONParser()
            query_result = [encoder.encode(resource) for resource in matches]

        return Response({
            "resource_descriptors": query_result
        }, status=httplib.OK)