"""Represent a descriptor of a resource."""
from __future__ import absolute_import

from inspect import isclass

from future.builtins import object

from rotest.management import ResourceData
from rotest.management.common.errors import ResourceBuildError
from rotest.management.common.utils import (TYPE_NAME,
                                            PROPERTIES,
                                            extract_type,
                                            extract_type_path)
import six


class ResourceDescriptor(object):
    """Holds the data for a resource request."""
    def __init__(self, resource_type, **properties):
        """Initialize the required parameters of resource request.

        Args:
            resource_type (type): resource type.
            properties (kwargs): properties of the resource.
        """
        self.type = resource_type
        self.properties = properties

    def __repr__(self):
        """Returns the descriptor's repr string."""
        type_name = self.type.__name__
        keywords = ', '.join(['%s=%r' % (key, val)
                              for key, val in six.iteritems(self.properties)])
        return "%s(%s)" % (type_name, keywords)

    def build_resource(self):
        """Build a resource.

        Returns:
            rotest.common.models.base_resource.BaseResource. a resource.

        Raises:
            ResourceBuildError: Failed to build the resource with given params.
        """
        try:
            return self.type(**self.properties)

        except TypeError as ex:
            raise ResourceBuildError('Failed to build resource. Original error'
                                     'was: "%s"' % ex)

    def encode(self):
        """Build a dictionary that represent the ResourceDescriptor.

        Returns:
            dict. the corresponding dictionary.
        """
        if isclass(self.type) and issubclass(self.type, ResourceData):
            name = extract_type_path(self.type)

        else:
            name = extract_type_path(self.type.DATA_CLASS)

        return {TYPE_NAME: name, PROPERTIES: self.properties}

    @staticmethod
    def decode(descriptor):
        """Build a ResourceDescriptor from the given dictionary.

        Args:
            descriptor (dict): a dictionary that represent a descriptor.
                For instance: {'type': 'my_res', 'properties': {'key1': 1}}.

        Returns:
            ResourceDescriptor. the corresponding ResourceDescriptor.

        Raises:
            ValueError: given dictionary missing a relevant key.
        """
        for key in (TYPE_NAME, PROPERTIES):
            if key not in descriptor:
                raise ValueError("'descriptor' %r missing key %r" %
                                 (descriptor, key))

        type_name = descriptor[TYPE_NAME]
        resource_type = extract_type(type_name)

        properties = descriptor[PROPERTIES]

        return ResourceDescriptor(resource_type, **properties)
