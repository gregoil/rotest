import httplib
import json

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rotest.common.django_utils.common import get_sub_model
from rotest.management import ResourceData
from rotest.management.common.errors import ResourceAlreadyAvailableError, \
    ResourcePermissionError, ServerError, ResourceReleaseError, \
    ResourceDoesNotExistError
from rotest.api.constants import RESPONSE_PAGE_NOT_IMPLEMENTED
from rotest.management.common.utils import get_username


def _release_resource(resource, user_name):
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
            _release_resource(sub_resource, user_name)

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


@csrf_exempt
@transaction.atomic
def release_resources(request, *args, **kwargs):
    """Release the given resources one by one."""
    if request.method != "POST":
        return JsonResponse(RESPONSE_PAGE_NOT_IMPLEMENTED,
                            status=httplib.BAD_REQUEST)

    errors = {}
    body = json.loads(request.body)
    username = get_username(request)
    for name in body["resources"]:
        try:
            resource_data = ResourceData.objects.get(name=name)

        except ObjectDoesNotExist:
            errors[name] = (ResourceDoesNotExistError.ERROR_CODE,
                            "Resource %r doesn't exist" % name)
            continue

        resource = get_sub_model(resource_data)

        try:
            _release_resource(resource, username)

        except ServerError as ex:
            errors[name] = (ex.ERROR_CODE, ex.get_error_content())

    if len(errors) > 0:
        return JsonResponse({
            "errors": errors,
            "details": "errors occurred while releasing resource"
        }, status=httplib.BAD_REQUEST)

    return JsonResponse({}, status=httplib.NO_CONTENT)
