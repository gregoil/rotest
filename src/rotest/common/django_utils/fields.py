"""Contain common module fields."""
# pylint: disable=too-many-public-methods
from __future__ import absolute_import
import re

from django.db import models
from django.core.exceptions import ValidationError


class NameField(models.CharField):
    """Item name string field.

    This field is limited to 64 characters and contains the name(string).

    Good examples:

    * "name_lastname"
    * "name@lasrname"
    * 64 characters name

    Bad examples:

    * 65 characters name
    """
    MAX_LEN = 150

    def __init__(self, max_length=MAX_LEN, *args, **kwargs):
        super(NameField, self).__init__(*args, max_length=max_length,
                                        **kwargs)


class DynamicIPAddressField(models.CharField):
    """DNS name or IP address."""
    MAX_LEN = 64

    def __init__(self, max_length=MAX_LEN, *args, **kwargs):
        super(DynamicIPAddressField, self).__init__(*args,
                                                    max_length=max_length,
                                                    **kwargs)


class MACAddressField(models.CharField):
    """MAC address field."""
    MAX_LEN = 17  # enables writing exactly 16 characters
    MAC_ADDRESS_REGEX = '(([0-9a-fA-F]{2}):){5}[0-9a-fA-F]{2}'

    def __init__(self, max_length=MAX_LEN, *args, **kwargs):
        super(MACAddressField, self).__init__(*args,
                                              max_length=max_length,
                                              **kwargs)

    def validate(self, value, model_instance):
        """Validate that the input value is a MAC address."""
        super(MACAddressField, self).validate(value, model_instance)

        if re.match(self.MAC_ADDRESS_REGEX, value) is None:
            raise ValidationError('The input MAC address does not match the '
                                  'pattern of a MAC address')


class PathField(models.CharField):
    r"""File-system path string field.

    This field is limited to 200 characters and contains string path split by
    slashes or backslashes.

    Good examples:

    * "/mnt/home/code/a.txt"
    * "/./a"
    * "c:\\windows\\temp"

    Bad examples:

    * "//mnt//@%$2"
    * "c:\;"
    """
    MAX_LEN = 200

    def __init__(self, max_length=MAX_LEN, *args, **kwargs):
        super(PathField, self).__init__(*args, max_length=max_length,
                                        **kwargs)


class VersionField(models.CharField):
    """Item version string field.

    This field is limited to 10 characters and contains numbers and characters
    separated by dots.

    Good examples:

    * "4.12F"
    * "1.1423"

    Bad examples:

    * "4,12F"
    * "1/1423"
    """
    MAX_LEN = 10

    def __init__(self, max_length=MAX_LEN, *args, **kwargs):
        super(VersionField, self).__init__(*args, max_length=max_length,
                                           **kwargs)


class PortField(models.PositiveSmallIntegerField):
    """Port number field (for IP connections)."""
    pass
