import os
import json
import httplib
import re

from django.http import JsonResponse
from django.shortcuts import render

BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))


def swagger_file(request, *args, **kwargs):
    with open(os.path.join(BASE_FOLDER, "swagger.json"), "r") as swagger_json:
        swagger = json.load(swagger_json)

    match = re.match(r"(?P<base_path>.*/api/).*", request.get_full_path())
    swagger["basePath"] = match.group("base_path")

    return JsonResponse(swagger, status=httplib.OK)


def index(request, *args, **kwargs):
    return render(request, "swagger.html")
