# pylint: disable=unused-argument, no-self-use, too-many-locals
from __future__ import absolute_import

from datetime import datetime

from six.moves import http_client
from future.builtins import next
from django.db import transaction
from django.db.models.query_utils import Q
from django.core.exceptions import FieldError
from django.contrib.auth import models as auth_models
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.exceptions import BadRequest
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.management.common.utils import get_username
from rotest.management.common.parsers import JSONParser
from rotest.management.common.errors import ResourceTypeError
from rotest.api.common.models import LockResourcesParamsModel
from rotest.api.test_control.middleware import session_middleware
from rotest.management.common.resource_descriptor import ResourceDescriptor
from rotest.api.common.responses import (InfluencedResourcesResponseModel,
                                         FailureResponseModel)


USER_NOT_EXIST = "User {} has no matching object in the DB"
INVALID_RESOURCES = "No existing resource meets the requirements: {!r}"
UNAVAILABLE_RESOURCES = "No available resource meets the requirements: {!r}"


class LockResources(DjangoRequestView):
    """Lock the given resources one by one.

    Note:
        If one of the resources fails to lock, all the resources
        that has been locked until that resource will be released.
    """
    URI = "resources/lock_resources"
    DEFAULT_MODEL = LockResourcesParamsModel
    DEFAULT_RESPONSES = {
        http_client.OK: InfluencedResourcesResponseModel,
        http_client.BAD_REQUEST: FailureResponseModel
    }
    TAGS = {
        "post": ["Resources"]
    }

    def _lock_resource(self, resource, user_name):
        """Mark the resource as locked by the given user.

        For complex resource, marks also its sub-resources as locked by the
        given user.

        Args:
            resource (ResourceData): resource to lock.
            user_name (str): name of the locking user.
        """
        for sub_resource in resource.get_sub_resources():
            self._lock_resource(sub_resource, user_name)

        resource.owner = user_name
        resource.owner_time = datetime.now()
        resource.save()

    def _get_available_resources(self, descriptor, username, groups):
        """Get the potential resources to be locked that fits the descriptor.

        Args:
            descriptor (ResourceDescriptor): a descriptor of the wanted
                resource.
            username (str): the user who wants to lock the resource.
            groups (list): list of the resource groups that the resource
                should be taken from.

        Raises:
            BadRequest. if the descriptor given is invalid or the are no
                resources to be locked.

        Returns:
            generator. generator of resources that can be locked and are
                available to the user who requested them.
        """
        # query for resources that are usable and match the user's
        # preference, which are either belong groups he's in or
        # don't belong to any group.
        query = (Q(is_usable=True, **descriptor.properties) &
                 (Q(group__isnull=True) | Q(group__in=groups)))
        try:
            matches = descriptor.type.objects.select_for_update() \
                .filter(query).order_by('-reserved')

        except FieldError as e:
            raise BadRequest(str(e))

        if matches.count() == 0:
            raise BadRequest(INVALID_RESOURCES.format(descriptor))

        return (resource for resource in matches
                if resource.is_available(username))

    def _try_to_lock_available_resource(self, username, groups,
                                        descriptor_dict):
        """Try to lock one of the given available resources.

        Args:
            descriptor_dict (dict): a descriptor dict of the wanted resource.
                Example:
                    {
                        "type": "resourceData",
                        "properties": {}
                    }
            username (str): the user who wants to lock the resource.
            groups (list): list of the resource groups that the resource
                should be taken from.

        Returns:
            ResourceData. the locked resource.

        Raises:
            BadRequest. If there are no available resources.
        """
        try:
            descriptor = ResourceDescriptor.decode(descriptor_dict)

        except ResourceTypeError as e:
            raise BadRequest(str(e))

        availables = self._get_available_resources(
            descriptor, username, groups)

        try:
            resource = next(availables)
            self._lock_resource(resource, username)
            return resource

        except StopIteration:
            raise BadRequest(UNAVAILABLE_RESOURCES.format(descriptor))

    @session_middleware
    def post(self, request, sessions, *args, **kwargs):
        """Lock the given resources one by one.

        Note:
            If one of the resources fails to lock, all the resources that has
            been locked until that resource will be released.
        """
        try:
            session = sessions[request.model.token]

        except KeyError:
            raise BadRequest("Invalid token/test_id provided!")

        username = get_username(request)
        descriptors = request.model.descriptors

        if not auth_models.User.objects.filter(username=username).exists():
            raise BadRequest(USER_NOT_EXIST.format(username))

        locked_resources = []
        user = auth_models.User.objects.get(username=username)
        groups = list(user.groups.all())
        with transaction.atomic():
            for descriptor_dict in descriptors:
                locked_resources.append(self._try_to_lock_available_resource(
                    username, groups, descriptor_dict))

        for resource in locked_resources:
            session.resources.append(resource)

        encoder = JSONParser()
        response = [encoder.recursive_encode(_resource)
                    for _resource in locked_resources]
        return Response({
            "resource_descriptors": response
        }, status=http_client.OK)
