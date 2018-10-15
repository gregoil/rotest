# pylint: disable=unused-argument, no-self-use
from __future__ import absolute_import
import six.moves.http_client

from django.db import transaction
from django.db.models.query_utils import Q
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.exceptions import BadRequest
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.management.common.errors import ResourceTypeError
from rotest.management.common.json_parser import JSONParser
from rotest.api.common.models import ResourceDescriptorModel
from rotest.management.common.resource_descriptor import ResourceDescriptor
from rotest.api.common.responses import (InfluencedResourcesResponseModel,
                                         FailureResponseModel)


class QueryResources(DjangoRequestView):
    """Find and return the resources that answer the client's query.

    Returns:
        ResourcesReply. a reply containing matching resources.
    """
    URI = "resources/query_resources"
    DEFAULT_MODEL = ResourceDescriptorModel
    DEFAULT_RESPONSES = {
        six.moves.http_client.OK: InfluencedResourcesResponseModel,
        six.moves.http_client.BAD_REQUEST: FailureResponseModel
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
            descriptor = ResourceDescriptor.decode(request.model.obj)

        except ResourceTypeError as e:
            raise BadRequest(str(e))

        # query for resources that are usable and match the descriptors
        query = (Q(is_usable=True, **descriptor.properties))
        query_result = []
        with transaction.atomic():
            matches = descriptor.type.objects.select_for_update().filter(query)

            if matches.count() == 0:
                raise BadRequest("No existing resource meets "
                                 "the requirements: {!r}".format(descriptor))

            encoder = JSONParser()
            query_result = [encoder.encode(resource) for resource in matches]

        return Response({
            "resource_descriptors": query_result
        }, status=six.moves.http_client.OK)
