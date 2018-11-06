"""JSON parser module.

Note:
    Django works with Unicode therefore, we use here basestring which is the
    base class of unicode and str type.
"""
# pylint: disable=too-many-return-statements,protected-access,too-many-locals
from __future__ import absolute_import

from numbers import Number

from six import string_types
from future.utils import iteritems
from django.db import models
from django.db.models import ForeignKey

from rotest.management.common import messages
from rotest.management.base_resource import BaseResource
from rotest.management.common.parsers.abstract_parser import ParsingError
from rotest.management.common.utils import (TYPE_NAME, DATA_NAME, PROPERTIES,
                                            extract_type, extract_type_path)
from .abstract_parser import AbstractParser


class JSONParser(AbstractParser):
    """json messages parser.

    This message parser allows to encode & decode resource management messages.
    Each message should be composed from basic-types (such as numbers, strings
    and booleans), lists, dictionaries, and resources (which derived from
    :class:`BaseResource`).

    Any other object type may cause an error during the encoding process.
    The result of successful encoding process is an json string, represent the
    encoded message.

    When decoding data (an json string), the parser validates it using the
    parser's scheme. Failure in the validation case will cause a raise of
    ParsingError exception.


    Attributes:
        complex_decoders (dict): map element type to its decoding method.
    """
    _NONE_TYPE = 'None'
    _LIST_TYPE = 'List'
    _CLASS_TYPE = 'Class'
    _DICT_TYPE = 'Dictionary'
    _RESOURCE_TYPE = 'Resource'
    _RESOURCE_DATA_TYPE = 'ResourceData'

    def __init__(self):
        super(JSONParser, self).__init__()
        self.complex_decoders = {
            self._LIST_TYPE: self._decode_list,
            self._DICT_TYPE: self._decode_dict,
            self._CLASS_TYPE: self._decode_class,
            self._RESOURCE_TYPE: self._decode_resource,
            self._RESOURCE_DATA_TYPE: self._decode_resource_data
        }
        self.complex_encoders = {
            dict: self._encode_dict,
            list: self._encode_list,
            tuple: self._encode_list,
            type: self._encode_class,
            models.Model: self._encode_resource_data,
            BaseResource: self._encode_resource
        }

    def _encode_message(self, message):
        """Encode a message to JSON-compatible format.

        Args:
            message (AbstractMessage): message to encode.

        Returns:
            object. JSON compatible encoded object.
        """
        encoded_message = {"message_type": message.__class__.__name__}
        for slot in message.__slots__:
            slot_value = getattr(message, slot)
            encoded_message[slot] = self.recursive_encode(slot_value)

        return encoded_message

    def _decode_message(self, data):
        """Decode a message from JSON format.

        Args:
            data (object): message to decode.

        Returns:
            AbstractMessage. message after decoding from json.
        """
        message_class = getattr(messages, data.pop("message_type"))
        kwargs = {key: self.recursive_decode(value)
                  for key, value in data.items()}

        return message_class(**kwargs)

    def recursive_encode(self, data):
        """Encode the given data according to its type.

        Warning:
            Do not change the order of the type validation! Some types matches
            more than one type (e.g: bool is also a Number).

        Args:
            data (object): an object to encode.

        Returns:
            object. encoded data, depends on the parser type.

        Raises:
            TypeError: given 'data' couldn't be encoded by this parser.
        """
        if data is None:
            return self._NONE_TYPE

        base_types = [string_types, bool, Number]

        for encoder_type in base_types:
            if isinstance(data, encoder_type):
                return data

        for encoder_type, encoder_handler in \
                list(iteritems(self.complex_encoders)):
            if isinstance(data, encoder_type):
                return encoder_handler(data)

        raise TypeError("Type %r isn't supported by the parser" % type(data))

    def _encode_resource(self, resource):
        """Encode a resource to an json string.

        Args:
            resource (BaseResource): resource to encode.

        Returns:
            dict. json element represent a resource.
        """
        type_name = extract_type_path(type(resource))

        return {
            self._RESOURCE_TYPE: {
                TYPE_NAME: self.recursive_encode(type_name),
                DATA_NAME: self.recursive_encode(resource.data)
            }
        }

    def _encode_resource_data(self, resource_data):
        """Encode resource data to an json string.

        Args:
            resource_data (ResourceData): resource to encode.

        Returns:
            dict. json element represent a resource.
        """
        type_name = extract_type_path(type(resource_data))

        return {
            self._RESOURCE_DATA_TYPE: {
                TYPE_NAME: self.recursive_encode(type_name),
                PROPERTIES: self.recursive_encode(resource_data.get_fields())
            }
        }

    def _encode_class(self, data_type):
        """Encode a class to an json string.

        Args:
            data_type (type): class to encode.

        Returns:
            dict. json element represent the class.
        """
        return {
            self._CLASS_TYPE: {
                TYPE_NAME: self.recursive_encode(extract_type_path(data_type))
            }
        }

    def _encode_dict(self, dict_data):
        """Encode a dictionary to an json string.

        Args:
            dict_data (dict): dictionary to encode.

        Returns:
            dict. json element represent a dictionary.

        Raises:
            ParsingError: one of the keys is not of type str.
        """
        dict_return = {}

        for key, value in iteritems(dict_data):
            if not isinstance(key, string_types):
                raise ParsingError("Failed to encode dictionary, "
                                   "key %r is not a string" % key)

            dict_return[key] = self.recursive_encode(value)

        return {
            self._DICT_TYPE: dict_return
        }

    def _encode_list(self, list_data):
        """Encode a list to an json string.

        Args:
            list_data (list): list to encode.

        Returns:
            dict. json element represent a list.
        """
        list_data = \
            [self.recursive_encode(item) for item in list_data]
        return {
            self._LIST_TYPE: list_data
        }

    def recursive_decode(self, element):
        """Decode an JSON element according to its inner type.

        Args:
            element (object): an JSON element.

        Returns:
            object. decoded object.

        Raises:
            ParsingError: failed to decode the element.
        """
        if not isinstance(element, dict) or \
                        list(element.keys())[0] not in self.complex_decoders:
            value = element

            if value == self._NONE_TYPE:
                return None

            if isinstance(value, string_types):
                return value

            if isinstance(value, (bool, Number)):
                return value

        decoder_type = list(element.keys())[0]

        decoder = self.complex_decoders[decoder_type]
        return decoder(element[decoder_type])

    def _decode_resource_data(self, resource_element):
        """Decode a resource element.

        Args:
            resource_element (dict): an json element that represent a
                resource.

        Returns:
            BaseResource. decoded resource.
        """
        type_element = resource_element[TYPE_NAME]
        type_name = self.recursive_decode(type_element)
        resource_type = extract_type(type_name)

        properties_element = resource_element[PROPERTIES]
        resource_properties = self.recursive_decode(properties_element)

        # Get the related fields.
        list_field_names = [
            key for key, value in iteritems(resource_properties)
            if isinstance(value, list)]

        list_fields = [(field_name, resource_properties.pop(field_name))
                       for field_name in list_field_names]

        resource = resource_type(**resource_properties)
        for field in resource._meta.fields:
            if isinstance(field, ForeignKey):
                if hasattr(resource, field.name):
                    field_value = getattr(resource, field.name)
                    if field_value:
                        setattr(resource, "{}_id".format(field.name),
                                field_value.id)

        for field_name, field_values in list_fields:
            # Set the related fields' values.
            field_object, _, is_direct, is_many_to_many = \
                resource_type._meta.get_field_by_name(field_name)

            if is_direct:
                raise ParsingError("Got unsupported direct list field %r" %
                                   field_name)

            if is_many_to_many:
                raise ParsingError("Got unsupported many to many field %r" %
                                   field_name)

            for related_object in field_values:
                # Set the related model's pointer to the current model.
                setattr(related_object, field_object.field.name, resource)

        return resource

    def _decode_resource(self, resource_element):
        """Decode a resource element.

        Args:
            resource_element (dict): an json element that represent a
                resource.

        Returns:
            BaseResource. decoded resource.
        """
        type_element = resource_element[TYPE_NAME]
        type_name = self.recursive_decode(type_element)
        resource_type = extract_type(type_name)

        data_element = resource_element[DATA_NAME]
        resource_data = self.recursive_decode(data_element)

        resource = resource_type(data=resource_data)

        return resource

    def _decode_class(self, class_element):
        """Decode a class element.

        Args:
            class_element (dict): an json element that represent a
                class.

        Returns:
            type. decoded class.
        """
        type_element = class_element[TYPE_NAME]
        type_path = self.recursive_decode(type_element)
        return extract_type(type_path)

    def _decode_dict(self, dict_element):
        """Decode a dictionary element.

        Args:
            dict_element (dict): an json element that represent a dict.

        Returns:
            dict. decoded dictionary.`
        """
        dictionary = {}
        for key, value in list(dict_element.items()):
            dictionary[key] = self.recursive_decode(value)

        return dictionary

    def _decode_list(self, list_element):
        """Decode a list element.

        Args:
            list_element (list): an json element that represent a list.

        Returns:
            list. decoded list.
        """
        return [self.recursive_decode(item) for item in list_element]
