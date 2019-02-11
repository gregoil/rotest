"""Represent a descriptor of a resource."""
from __future__ import absolute_import

from inspect import isclass

import six
from future.builtins import object

from rotest.management import ResourceData
from rotest.management.common.utils import (TYPE_NAME,
                                            FILTERS,
                                            extract_type,
                                            extract_type_path)


class ResourceDescriptor(object):
    """Holds the data for a resource request."""
    def __init__(self, resource_type, properties={}, **filters):
        """Initialize the required parameters of resource request.

        Args:
            resource_type (type): resource type.
            filters (dict): filters to apply when requesting the resource.
            properties (dict): initialization parameters for the resource.
        """
        self.type = resource_type
        self.filters = filters
        self.properties = properties

    def __repr__(self):
        """Returns the descriptor's repr string."""
        type_name = self.type.__name__
        filters = ', '.join(['%s=%r' % (key, val)
                            for key, val in six.iteritems(self.filters)])

        properties = ', '.join(['%s=%r' % (key, val)
                               for key, val in six.iteritems(self.properties)])

        return "%s(filters=%s)(properties=%s)" % (type_name, filters,
                                                  properties)

    def encode(self):
        """Build a dictionary that represent the ResourceDescriptor.

        Returns:
            dict. the corresponding dictionary.
        """
        if isclass(self.type) and issubclass(self.type, ResourceData):
            name = extract_type_path(self.type)

        else:
            name = extract_type_path(self.type.DATA_CLASS)

        return {TYPE_NAME: name, FILTERS: self.filters}

    @staticmethod
    def decode(descriptor):
        """Build a ResourceDescriptor from the given dictionary.

        Args:
            descriptor (dict): a dictionary that represent a descriptor.
                For instance: {'type': 'my_res', 'filters': {'key1': 1}}.

        Returns:
            ResourceDescriptor. the corresponding ResourceDescriptor.

        Raises:
            ValueError: given dictionary missing a relevant key.
        """
        for key in (TYPE_NAME, FILTERS):
            if key not in descriptor:
                raise ValueError("'descriptor' %r missing key %r" %
                                 (descriptor, key))

        type_name = descriptor[TYPE_NAME]
        resource_type = extract_type(type_name)

        filters = descriptor[FILTERS]

        return ResourceDescriptor(resource_type, **filters)
