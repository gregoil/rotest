"""Auxiliary module for discovering Rotest resources within an app."""
from __future__ import absolute_import
import os
from fnmatch import fnmatch

import py
import six
import django
from rotest.common.config import DISCOVERER_BLACKLIST
from rotest.management.base_resource import BaseResource


FILES_PATTERN = "*.py"


def _is_resource_class(item):
    """Check whether or not an object is a Rotest resource class.

    Args:
        item (object): object to check.

    Returns:
        bool. True if the given object is a Rotest resource, False otherwise.
    """
    return (isinstance(item, type) and issubclass(item, BaseResource) and
            item is not BaseResource)


def _import_resources_from_module(module_path):
    """Return all resources in the module.

    Args:
        module_path (str): relative path to the module.

    Returns:
        dict. all resource classes found in the module {name: class}.
    """
    if not fnmatch(module_path, FILES_PATTERN):
        return

    module = py.path.local(module_path).pyimport()

    return {item.__name__: item for item in six.itervalues(module.__dict__)
            if _is_resource_class(item)}


def get_resources(app_name, blacklist=DISCOVERER_BLACKLIST):
    """Get all the resource classes under a Django app.

    Args:
        app_name (str): application to search for resources inside.
        blacklist (tuple): module patterns to ignore.

    Returns:
        dict. all resource classes found in the application {name: class}.
    """
    django.setup()
    app_configs = django.apps.apps.app_configs
    if app_name not in app_configs:
        raise RuntimeError("Application %r was not found" % app_name)

    app_path = app_configs[app_name].path
    resources = {}

    for sub_dir, _, modules in os.walk(app_path):
        for module_name in modules:
            module_path = os.path.join(sub_dir, module_name)
            if any(fnmatch(module_path, pattern) for pattern in blacklist):
                continue

            module_resources = _import_resources_from_module(module_path)
            if module_resources is not None:
                resources.update(module_resources)

    return resources
