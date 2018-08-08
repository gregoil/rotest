import inspect
import os
import json
import httplib
import re

from django.http import JsonResponse
from django.shortcuts import render

from rotest.management.common.requests import REQUESTS
from rotest.management.common.requests.base_api import (AbstractAPIArray,
                                                        AbstractAPIModel)

BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))


class SwaggerBuilder(object):

    def __init__(self):
        self.models = {}

    def _parse_type(self, type_name):
        premative_types = [
            "array",
            "object",
            "string",
            "integer"
        ]

        if type_name not in premative_types:
            mod = __import__('rotest.management.common.requests',
                             fromlist=[type_name])
            klass = getattr(mod, type_name)

            return klass

        else:
            return type_name

    def _build_model_properties(self, properties):
        return_dict = {}
        for property in properties:
            property.TYPE = self._parse_type(property.TYPE)
            return_dict[property.NAME] = {
                "type": property.TYPE
            }
            if issubclass(property, AbstractAPIArray):
                return_dict[property.NAME].update({
                    "items": {
                        "$ref": self._get_model_referance(property.ITEMS_TYPE)
                    }
                })

        return return_dict

    def _build_model(self, model):
        self.models[model.__name__] = {
            "title": model.TITLE,
            "description": model.__doc__,
            "type": "object",
            "properties": self._build_model_properties(model.PROPERTIES)
        }

    def _get_model_referance(self, model):
        if not model.TITLE in self.models:
            self._build_model(model)

        return "#/components/schemas/{}".format(model.__name__)

    def  _build_parameters(self, parameters):
        parameters_list = []
        for parameter in parameters:
            parameter.TYPE = self._parse_type(parameter.TYPE)
            current_parameter = {
                "name": parameter.NAME,
                "in": "body",
                "description": parameter.__doc__,
                "required": parameter.REQUIRED,
                "schema": {
                    "type": parameter.TYPE
                }
            }
            if inspect.isclass(parameter.TYPE) and \
                    issubclass(parameter.TYPE, AbstractAPIModel):
                current_parameter["schema"].update({
                    "$ref": self._get_model_referance(parameter.TYPE)
                })

            elif issubclass(parameter, AbstractAPIArray):
                current_parameter["schema"].update({
                    "items": {
                        "$ref": self._get_model_referance(
                            self._parse_type(parameter.ITEMS_TYPE))
                    }
                })

            parameters_list.append(current_parameter)

        return parameters_list

    def _build_responses(self, responses):
        return_dict = {}
        for response_code, response_model in responses.items():
            return_dict[response_code] = {
                "description": "No Content",
                "content": {
                    "application/json": {
                        "schema": {}
                    }
                }
            }
            if response_model is not None:
                return_dict[response_code]["description"] = \
                    response_model.__doc__
                content = \
                    return_dict[response_code]["content"]["application/json"]
                content["schema"] = {
                    "$ref": self._get_model_referance(response_model)
                }

        return return_dict

    def _build_swagger_methods(self, request):
        return {
            request.METHOD.lower(): {
                "tags": request.TAGS,
                "description": request.__doc__,
                "operationID": request.__name__,
                "parameters": self._build_parameters(request.PARAMS),
                "responses": self._build_responses(request.RESPONSES)
                }
            }

    def build_swagger(self):
        paths = {}
        for request in REQUESTS:
            paths[request.URI] = self._build_swagger_methods(request)

        return paths, self.models


def swagger_file(request, *args, **kwargs):
    with open(os.path.join(BASE_FOLDER, "swagger.json"), "r") as swagger_json:
        swagger = json.load(swagger_json)

    match = re.match(r"(?P<base_path>.*/api/).*", request.get_full_path())
    swagger["basePath"] = match.group("base_path")
    builder = SwaggerBuilder()
    paths, schemas = builder.build_swagger()
    swagger["paths"] = paths
    swagger["components"] = {
        "schemas": schemas
    }

    return JsonResponse(swagger, status=httplib.OK)


def index(request, *args, **kwargs):
    return render(request, "swagger.html")
