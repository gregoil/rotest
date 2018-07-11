""""Set a field of resource module."""
import json
from socket import gethostbyaddr

from django.http.response import JsonResponse
from rotest.management.models.resource_data import ResourceData


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")  # get forward ip
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]

    else:
        ip = request.META.get("REMOTE_ADDR")

    return ip


def lock_resource(request, data_name):
    """"Lock a specific given resource."""
    lock_function = set_field("reserved")
    user = gethostbyaddr(get_client_ip(request))[0]
    data = json.loads(lock_function(request, data_name, user).content)
    data["user"] = user
    return JsonResponse(data)


def set_field(field_name):
    """"Set a field recursively.

    Args:
        field_name (str): the field to set.

    Returns:
        function. a function that allows to set a value of a given field.
    """

    def set_resource_field(request, data_name, value=""):
        """"Entry point for removing any field from a resource.

        Args:
            request (HttpRequest): GET http request.
            data_name (str): the name of the resource.
            value (str): the value of the field to set to
                (default: "" - clear field).

        Returns:
            JsonResponse. the components that were changed.
        """
        effected_resource_head = \
            ResourceData.objects.filter(name=data_name)[0]
        effected_resources = _field_set_recursively(effected_resource_head,
                                                    field_name,
                                                    value)

        return JsonResponse({"effected_resources": effected_resources})

    return set_resource_field


def _field_set_recursively(resource, field_name, value):
    """Set a field for a given resource and all of its children.

    Args:
        resource (ResourceData): the resource to change.
        field_name (str): the field to set.
        value (str): the value of the field to set to.

    Returns:
        list. all the effected resources.
    """
    effected_resources = []
    for sub_resource in resource.leaf.get_sub_resources():
        set_resources = _field_set_recursively(sub_resource,
                                               field_name,
                                               value)
        effected_resources.extend(set_resources)

    setattr(resource, field_name, value)
    resource.save()

    effected_resources.append(resource.name)
    return effected_resources
