import httplib
import json

from datetime import datetime

from django.db.models.query_utils import Q
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth import models as auth_models
from django.views.decorators.csrf import csrf_exempt

from rotest.management.common.json_parser import JSONParser
from rotest.management.common.resource_descriptor import ResourceDescriptor
from rotest.api.constants import RESPONSE_PAGE_NOT_IMPLEMENTED
from rotest.management.common.utils import get_username


def _lock_resource(resource, user_name):
    """Mark the resource as locked by the given user.

    For complex resource, marks also its sub-resources as locked by the
    given user.

    Note:
        The given resource *must* be available.

    Args:
        resource (ResourceData): resource to lock.
        user_name (str): name of the locking user.
    """
    for sub_resource in resource.get_sub_resources():
        _lock_resource(sub_resource, user_name)

    resource.owner = user_name
    resource.owner_time = datetime.now()
    resource.save()


@csrf_exempt
@transaction.atomic
def lock_resources(request, *args, **kwargs):
    """Lock the given resources one by one.

    Note:
        If one of the resources fails to lock, all the resources that has
        been locked until that resource will be released.
    """
    if request.method != "POST":
        return JsonResponse(RESPONSE_PAGE_NOT_IMPLEMENTED,
                            status=httplib.BAD_REQUEST)

    locked_resources = []
    user_name = get_username(request)
    body = json.loads(request.body)
    descriptors = body["descriptors"]

    if not auth_models.User.objects.filter(username=user_name).exists():
        return JsonResponse({
            "details": "User {} has no matching object in the DB".format(
                user_name)
        }, status=httplib.BAD_REQUEST)

    user = auth_models.User.objects.get(username=user_name)

    groups = list(user.groups.all())

    for descriptor_dict in descriptors:

        desc = ResourceDescriptor.decode(descriptor_dict)
        # query for resources that are usable and match the user's
        # preference, which are either belong to a group he's in or
        # don't belong to any group.
        query = (Q(is_usable=True, **desc.properties) &
                 (Q(group__isnull=True) | Q(group__in=groups)))
        matches = desc.type.objects.filter(query).order_by('-reserved')

        if matches.count() == 0:
            return JsonResponse({
                "details": "No existing resource meets "
                           "the requirements: {!r}".format(desc)
            }, status=httplib.BAD_REQUEST)

        availables = (resource for resource in matches
                      if resource.is_available(user_name))

        try:
            resource = availables.next()

            _lock_resource(resource, user_name)
            locked_resources.append(resource)

        except StopIteration:
            return JsonResponse({
                "details": "No available resource meets "
                           "the requirements: {!r}".format(desc)
            }, status=httplib.BAD_REQUEST)

    parser = JSONParser()
    response = [parser.encode(resource) for resource in locked_resources]
    return JsonResponse({
        "resources": response
    }, status=httplib.OK)
