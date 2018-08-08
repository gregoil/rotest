import httplib
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rotest.management import ResourceData
from rotest.api.constants import RESPONSE_PAGE_NOT_IMPLEMENTED


@csrf_exempt
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

    body = json.loads(request.body)
    model = body["model"]
    filter_dict = body["filter"]
    kwargs_vars = body["kwargs"]
    objects = model.objects
    if filter_dict is not None and len(filter_dict) > 0:
        objects.filter(**filter_dict).update(**kwargs_vars)

    else:
        objects.all().update(**kwargs_vars)

    return JsonResponse({}, status=httplib.NO_CONTENT)
