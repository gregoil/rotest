import httplib
import os

import requests

BASE_API = "api/"


class AbstractRequest(object):
    URI = NotImplemented
    METHOD = NotImplemented
    TAGS = []
    PARAMS = []
    RESPONSES = {}

    def __init__(self, data):
        self.data = data

    def execute(self, base_url, logger):
        url = os.path.join(base_url, self.URI)
        logger.debug("request: %s - %s - %s", url, self.METHOD, self.data)

        response = requests.request(self.METHOD, url, json=self.data)

        logger.debug("response: %s(%s) - %s",
                     httplib.responses[response.status_code],
                     response.status_code,
                     response.content)

        return response


class AbstractField(object):
    NAME = NotImplemented
    TYPE = NotImplemented
    REQUIRED = True


class AbstractAPIModel(object):
    TITLE = NotImplemented
    PROPERTIES = []


class AbstractAPIArray(AbstractField):
    NAME = NotImplemented
    TYPE = "array"
    ITEMS_TYPE = NotImplemented


class Requester(object):
    def __init__(self, host, port, logger, base_url):
        self.base_url = os.path.join("http://{}:{}/".format(host, port),
                                     base_url, BASE_API)
        self.logger = logger

    def request(self, request_type, data):
        request = request_type(data)
        return request.execute(self.base_url, self.logger)
