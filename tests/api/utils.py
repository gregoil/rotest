"""API test utilities."""
# pylint: disable=too-many-arguments
from __future__ import absolute_import
import os
import json
import six.moves.urllib.request, six.moves.urllib.parse, six.moves.urllib.error

from attrdict import AttrDict


BASEPATH = "/rotest/api/"


def request(client, path, method="post",
            json_data=None,
            params=None,
            content_type="application/json"):
    """Make a request to the server and get json response if possible.

    Args:
        client (django.test.Client): client to make the requests with.
        path (str): url path of the request.
        method (str): the request method ["post", "get", etc..].
        params(dict): data to send to query dict.
        json_data (dict): json data to send with the request.
        content_type (str): the data's content type.
    """
    if json_data is not None:
        json_data = json.dumps(json_data)

    if params is not None:
        params = six.moves.urllib.parse.urlencode(params)

    response = client.generic(method,
                              "{}?{}".format(os.path.join(BASEPATH, path),
                                             params),
                              data=json_data,
                              content_type=content_type)

    try:
        return response, AttrDict(json.loads(response.content))

    except ValueError:  # couldn't decode json object
        return response, response.content
