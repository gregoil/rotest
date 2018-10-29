# pylint: disable=unused-argument, no-self-use
from __future__ import absolute_import

from six.moves import http_client
from future.builtins import str
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.exceptions import BadRequest
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.management import ResourceData
from rotest.management.common.utils import get_username
from rotest.common.django_utils.common import get_sub_model
from rotest.api.common.models import ReleaseResourcesParamsModel
from rotest.api.test_control.middleware import session_middleware
from rotest.api.common.responses import (FailureResponseModel,
                                         SuccessResponse)
from rotest.management.common.errors import (ResourceAlreadyAvailableError,
                                             ResourceDoesNotExistError,
                                             ResourcePermissionError,
                                             ResourceReleaseError,
                                             ServerError)


class ReleaseResources(DjangoRequestView):
    """Release the given resources one by one.

    For complex resource, marks also its sub-resources as free.

    Raises:
        ResourceReleaseError: if resource is a complex resource and fails.
        ResourcePermissionError: if resource is locked by other user.
        ResourceAlreadyAvailableError: if resource was already available.
    """
    URI = "resources/release_resources"
    DEFAULT_MODEL = ReleaseResourcesParamsModel
    DEFAULT_RESPONSES = {
        http_client.NO_CONTENT: SuccessResponse,
        http_client.BAD_REQUEST: FailureResponseModel
    }
    TAGS = {
        "post": ["Resources"]
    }

    @classmethod
    def release_resource(cls, resource, username):
        """Mark the resource as free.

        For complex resource, marks also its sub-resources as free.

        Args:
            resource (ResourceData): resource to release.
            username (str): name of the releasing user.

        Raises:
            ResourceReleaseError: if resource is a complex resource and fails.
            ResourcePermissionError: if resource is locked by other user.
            ResourceAlreadyAvailableError: if resource was already available.
        """
        errors = {}

        for sub_resource in resource.get_sub_resources():
            try:
                cls.release_resource(sub_resource, username)

            except ServerError as ex:
                errors[sub_resource.name] = (ex.ERROR_CODE, str(ex))

        if username is not None and resource.is_available(username):
            raise ResourceAlreadyAvailableError("Failed releasing resource "
                                                "%r, it was not locked"
                                                % resource.name)

        if username is not None and resource.owner != username:
            raise ResourcePermissionError("Failed releasing resource %r, "
                                          "it is locked by %r"
                                          % (resource.name, resource.owner))

        resource.owner = ""
        resource.owner_time = None
        resource.save()

        if len(errors) != 0:
            raise ResourceReleaseError(errors)

    @session_middleware
    def post(self, request, sessions, *args, **kwargs):
        """Release the given resources one by one."""
        try:
            session = sessions[request.model.token]

        except KeyError:
            raise BadRequest("Invalid token/test_id provided!")

        errors = {}
        username = get_username(request)

        with transaction.atomic():
            for name in request.model.resources:
                try:
                    resource_data = ResourceData.objects.select_for_update() \
                        .get(name=name)

                except ObjectDoesNotExist:
                    errors[name] = (ResourceDoesNotExistError.ERROR_CODE,
                                    "Resource %r doesn't exist" % name)
                    continue

                resource = get_sub_model(resource_data)

                try:
                    self.release_resource(resource, username)
                    session.resources.remove(resource)

                except ServerError as ex:
                    errors[name] = (ex.ERROR_CODE, ex.get_error_content())

        if len(errors) > 0:
            return Response({
                "errors": errors,
                "details": "errors occurred while releasing resource"
            }, status=http_client.BAD_REQUEST)

        return Response({}, status=http_client.NO_CONTENT)
