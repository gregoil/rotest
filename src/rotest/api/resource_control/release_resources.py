import httplib

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from swagapi.api.wrapper import RequestView, Response, BadRequest

from rotest.api.common.models import (ResourcesModel)
from rotest.api.common.responses import \
    (BadRequestResponseModel, EmptyResponse)
from rotest.common.django_utils.common import get_sub_model
from rotest.management import ResourceData
from rotest.management.common.errors import (ResourceAlreadyAvailableError,
                                             ResourceDoesNotExistError,
                                             ResourcePermissionError,
                                             ResourceReleaseError,
                                             ServerError)
from rotest.management.common.utils import get_username


class ReleaseResources(RequestView):
    """Release the given resources one by one.

    For complex resource, marks also its sub-resources as free.

    Raises:
        ResourceReleaseError: if resource is a complex resource and fails.
        ResourcePermissionError: if resource is locked by other user.
        ResourceAlreadyAvailableError: if resource was already available.
    """
    URI = "resources/release_resources"
    DEFAULT_MODEL = ResourcesModel
    DEFAULT_RESPONSES = {
        httplib.NO_CONTENT: EmptyResponse,
    }
    TAGS = {
        "post": ["Resources"]
    }

    def _release_resource(self, resource, user_name):
        """Mark the resource as free.

        For complex resource, marks also its sub-resources as free.

        Args:
            resource (ResourceData): resource to release.
            user_name (str): name of the releasing user.

        Raises:
            ResourceReleaseError: if resource is a complex resource and fails.
            ResourcePermissionError: if resource is locked by other user.
            ResourceAlreadyAvailableError: if resource was already available.
        """
        errors = {}

        for sub_resource in resource.get_sub_resources():
            try:
                self._release_resource(sub_resource, user_name)

            except ServerError as ex:
                errors[sub_resource.name] = (ex.ERROR_CODE, str(ex))

        if resource.is_available(user_name):
            raise ResourceAlreadyAvailableError("Failed releasing resource "
                                                "%r, it was not locked"
                                                % resource.name)

        if resource.owner != user_name:
            raise ResourcePermissionError("Failed releasing resource %r, "
                                          "it is locked by %r"
                                          % (resource.name, resource.owner))

        resource.owner = ""
        resource.owner_time = None
        resource.save()

        if len(errors) != 0:
            raise ResourceReleaseError(errors)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """Release the given resources one by one."""
        errors = {}
        username = get_username(request)
        for name in request.model.resources:
            try:
                resource_data = ResourceData.objects.get(name=name)

            except ObjectDoesNotExist:
                errors[name] = (ResourceDoesNotExistError.ERROR_CODE,
                                "Resource %r doesn't exist" % name)
                continue

            resource = get_sub_model(resource_data)

            try:
                self._release_resource(resource, username)

            except ServerError as ex:
                errors[name] = (ex.ERROR_CODE, ex.get_error_content())

        if len(errors) > 0:
            raise BadRequest({
                "errors": errors,
                "details": "errors occurred while releasing resource"
            })

        return Response({}, status=httplib.NO_CONTENT)
