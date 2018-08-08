import httplib

from datetime import datetime

from django.core import serializers
from django.db.models.query_utils import Q
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth import models as auth_models

from rotest.management.common.resource_descriptor import ResourceDescriptor
from rotest.api.constants import RESPONSE_PAGE_NOT_IMPLEMENTED


@transaction.atomic
def query_resources(request, *args, **kwargs):
    """Find and return the resources that answer the client's query.

    Args:
        request (Request): QueryResources request.

    Returns:
        ResourcesReply. a reply containing matching resources.
    """
    if request.method != "GET":
        return JsonResponse(RESPONSE_PAGE_NOT_IMPLEMENTED,
                            status=httplib.BAD_REQUEST)

    desc = ResourceDescriptor.decode(request.GET.get("descriptors"))
    # query for resources that are usable and match the descriptors
    query = (Q(is_usable=True, **desc.properties))
    matches = desc.type.objects.filter(query)

    if matches.count() == 0:
        return JsonResponse({
            "details": "No existing resource meets "
                       "the requirements: {!r}".format(desc)
        }, status=httplib.BAD_REQUEST)

    query_result = [resource for resource in matches]

    return JsonResponse({
        "result": serializers.serialize("json", query_result)
    }, status=httplib.OK)
