import httplib
from datetime import datetime

from django.db import transaction
from django.db.models.query_utils import Q
from django.contrib.auth import models as auth_models
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.exceptions import BadRequest
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.management.common.utils import get_username
from rotest.management.common.json_parser import JSONParser
from rotest.api.common.models import DescribedResourcesPostModel
from rotest.api.common.responses import InfluencedResourcesResponseModel
from rotest.management.common.resource_descriptor import ResourceDescriptor


# pylint: disable=unused-argument, no-self-use, too-many-locals


class LockResources(DjangoRequestView):
    """Lock the given resources one by one.

    Note:
        If one of the resources fails to lock, all the resources
        that has
        been locked until that resource will be released.
    """
    URI = "resources/lock_resources"
    DEFAULT_MODEL = DescribedResourcesPostModel
    DEFAULT_RESPONSES = {
        httplib.OK: InfluencedResourcesResponseModel,
    }
    TAGS = {
        "post": ["Resources"]
    }

    def _lock_resource(self, resource, user_name):
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
            self._lock_resource(sub_resource, user_name)

        resource.owner = user_name
        resource.owner_time = datetime.now()
        resource.save()

    def post(self, request, *args, **kwargs):
        """Lock the given resources one by one.

        Note:
            If one of the resources fails to lock, all the resources that has
            been locked until that resource will be released.
        """
        locked_resources = []
        user_name = get_username(request)
        descriptors = request.model.descriptors

        if not auth_models.User.objects.filter(username=user_name).exists():
            raise BadRequest({
                "details": "User {} has no matching object in the "
                           "DB".format(user_name)})

        user = auth_models.User.objects.get(username=user_name)

        groups = list(user.groups.all())
        with transaction.atomic():
            for descriptor_dict in descriptors:
                try:
                    desc = ResourceDescriptor.decode(descriptor_dict)

                except Exception as e:
                    raise BadRequest({"details": e.message})
                # query for resources that are usable and match the user's
                # preference, which are either belong to a group he's in or
                # don't belong to any group.
                query = (Q(is_usable=True, **desc.properties) &
                         (Q(group__isnull=True) | Q(group__in=groups)))

                matches = desc.type.objects.select_for_update()\
                    .filter(query).order_by('-reserved')

                if matches.count() == 0:
                    raise BadRequest({
                        "details": "No existing resource meets "
                                   "the requirements: {!r}".format(desc)})

                availables = (resource for resource in matches
                              if resource.is_available(user_name))

                try:
                    resource = availables.next()
                    self._lock_resource(resource, user_name)
                    locked_resources.append(resource)

                except StopIteration:
                    raise BadRequest({
                        "details": "No available resource meets "
                                   "the requirements: {!r}".format(desc)})

        encoder = JSONParser()
        response = [encoder.encode(_resource)
                    for _resource in locked_resources]
        return Response({
            "resource_descriptors": response
        }, status=httplib.OK)
