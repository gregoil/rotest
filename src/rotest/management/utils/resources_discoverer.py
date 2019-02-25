"""Auxiliary module for discovering Rotest resources within an app."""
from __future__ import absolute_import

from importlib import import_module

import six
from django.conf import settings
from django.utils.module_loading import module_has_submodule

from rotest.management.base_resource import BaseResource


RESOURCES_MODULE_NAME = "resources"


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
    module = import_module(module_path)

    return {item.__name__: item for item in six.itervalues(module.__dict__)
            if _is_resource_class(item)}


def get_resources():
    """Get all the resource classes from apps declared in settings.py.

    Returns:
        dict. all resource classes found in the application {name: class}.
    """
    declared_apps = settings.INSTALLED_APPS
    resources = {}

    for app_name in declared_apps:
        app_module = import_module(app_name)

        if module_has_submodule(app_module, RESOURCES_MODULE_NAME):
            resources_module = '%s.%s' % (app_name, RESOURCES_MODULE_NAME)
            app_resources = _import_resources_from_module(resources_module)
            resources.update(app_resources)

    return resources
