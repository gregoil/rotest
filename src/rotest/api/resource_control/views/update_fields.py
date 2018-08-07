import httplib

from django.http import JsonResponse

from rotest.management import ResourceData
from rotest.api.constants import RESPONSE_PAGE_NOT_IMPLEMENTED


def update_fields(request, *args, **kwargs):
    """Update content in the server's DB.

    Args:
        model (type): Django model to apply changes on.
        filter (dict): arguments to filter by.
        kwargs_vars (dict): the additional arguments are the changes to apply on
            the filtered instances.
    """
    if request.method != "POST":
        return JsonResponse(RESPONSE_PAGE_NOT_IMPLEMENTED,
                            status=httplib.BAD_REQUEST)

    model = request.POST.get("model")
    filter_dict = request.POST.get("filter")
    kwargs_vars = request.POST.get("kwargs")
    objects = model.objects
    if filter_dict is not None and len(filter_dict) > 0:
        objects.filter(**filter_dict).update(**kwargs_vars)

    else:
        objects.all().update(**kwargs_vars)

    return JsonResponse({}, status=httplib.NO_CONTENT)
