"""Common resource management constants."""
# pylint: disable=exec-used
from __future__ import absolute_import
import importlib
from socket import gethostbyaddr

from rotest.management.common.errors import ResourceTypeError


MESSAGE_DELIMITER = '\r\n'
MESSAGE_MAX_LENGTH = 240000

TEST_ID_KEY = 'id'
TEST_NAME_KEY = 'name'
TEST_CLASS_CODE_KEY = 'class'
TEST_SUBTESTS_KEY = 'subtests'

TYPE_NAME = "type"
DATA_NAME = "data"
PROPERTIES = "properties"

LOCAL_IP = "127.0.0.1"
LOCALHOST = "localhost"


def get_client_ip(request):
    """Get client's ip address.

    Returns:
        str. ip address of the client.
    """
    ip_chain = request.META.get("HTTP_X_FORWARDED_FOR")  # forward ip
    if ip_chain:
        ip_address = ip_chain.split(",")[0]

    else:
        ip_address = request.META.get("REMOTE_ADDR")

    return ip_address


def get_host_name(ip_address):
    """Return the host name for the given address.

    Args:
        ip_address(str): IP address to convert.

    Returns:
        str. hostname for the IP address.
    """
    host, _, ip_list = gethostbyaddr(ip_address)
    # In case the server runs on a local machine with DNS aliases.
    if LOCAL_IP in ip_list:
        host = LOCALHOST

    return host


def get_username(request):
    """Return the username.

    Returns:
        str. the client dns name - is the client username.
    """
    return get_host_name(get_client_ip(request))


def extract_type(type_path):
    """Extract a type of a resource from the given type path.

    Note:
        Hook to import extended resources (defined in external package).

    Args:
        type_path (str): full path of the type.

    Returns:
        type. a type of a resource.

    Raises:
        ResourceTypeError: given type path doesn't exists.
    """
    try:
        module_name, type_name = type_path.rsplit('.', 1)
        module = importlib.import_module(module_name)

        return getattr(module, type_name)

    except Exception as ex:
        raise ResourceTypeError("Failed to extract type %r. Reason: %s."
                                % (type_path, ex))


def extract_type_path(object_type):
    """Extract the full path of the given type.

    Agrs:
        object_type (type): an object type.

    Returns:
        str. type full path.
    """
    return "%s.%s" % (object_type.__module__, object_type.__name__)
