"""XML parser module.

Note:
    Django works with Unicode therefore, we use here basestring which is the
    base class of unicode and str type.
"""
# pylint: disable=too-many-return-statements,protected-access,too-many-locals
import os
from numbers import Number

from django.db import models
from lxml import etree, objectify, builder

from rotest.management.common import messages
from rotest.management.base_resource import BaseResource
from rotest.management.common.parsers.abstract_parser import \
                                            ParsingError, AbstractParser
from rotest.management.common.utils import (TYPE_NAME, DATA_NAME, PROPERTIES,
                                            extract_type, extract_type_path)


class XMLParser(AbstractParser):
    """XML messages parser.

    This message parser allow to encode & decode resource management messages.
    Each message should be composed from basic-types (such as numbers, strings
    and booleans), lists, dictionaries, and resources (which derived from
    :class:`BaseResource`).

    Any other object type may cause an error during the encoding process.
    The result of successful encoding process is an XML string, represent the
    encoded message.

    For instance, the inner message object:
        [False, {'key1': 5, 'key2': 'google'}, [1, 2, 3]]
    will be encoded as:

    <List>
        <Item>false</Item>
        <Item>
            <Dictionary>
                <key1>5</key1>
                <key2>"google"</key2>
            </Dictionary>
        </Item>
        <Item>
            <List>
                <Item>1</item>
                <Item>2</item>
                <Item>3</item>
            </List>
        </Item>
    </List>

    When decoding data (an XML string), the parser validates it using the
    parser's scheme. Failure in the validation case will cause a raise of
    ParsingError exception.


    Attributes:
        scheme (lxml.etree.XMLSchema): a scheme to validate messages with.
        complex_decoders (dict): map element type to its decoding method.
    """
    _NONE_TYPE = 'None'
    _LIST_TYPE = 'List'
    _CLASS_TYPE = 'Class'
    _LIST_ITEM_TYPE = 'Item'
    _DICT_TYPE = 'Dictionary'
    _RESOURCE_TYPE = 'Resource'
    _RESOURCE_DATA_TYPE = 'ResourceData'

    _SCHEME_FILE_NAME = "xml_parser_scheme.xsd"
    _SCHEME_PATH = os.path.join(os.path.dirname(__file__), "schemas",
                                _SCHEME_FILE_NAME)

    def __init__(self):
        super(XMLParser, self).__init__()
        self.scheme = etree.XMLSchema(file=self._SCHEME_PATH)

        self.complex_decoders = {
                         self._LIST_TYPE: self._decode_list,
                         self._DICT_TYPE: self._decode_dict,
                         self._CLASS_TYPE: self._decode_class,
                         self._RESOURCE_TYPE: self._decode_resource,
                         self._RESOURCE_DATA_TYPE: self._decode_resource_data}

    def _encode_message(self, message):
        """Encode a message to XML string.

        Args:
            message (AbstractMessage): a message to encode.

        Returns:
            str. XML string that represent the encoded message.
        """
        header = builder.E(message.__class__.__name__)

        for slot in message.__slots__:
            slot_value = getattr(message, slot)

            # BasicStruct handle None slots.
            slot_element = builder.E(slot, self._encode(slot_value))
            header.append(slot_element)

        return etree.tostring(header)

    def _decode_message(self, data):
        """Decode a message from an XML string.

        Args:
            data (str): data to decode. data is an XML string that represent an
                'AbstractMessage' object.

        Returns:
            AbstractMessage. decoded message.

        Raises:
            ParsingError: scheme validation failed.
            AttributeError: message tag name is not a valid message class name.
                the scheme should validate that this case will never happen.
        """
        root = objectify.XML(data)

        if not self.scheme.validate(root):
            scheme_errors = self.scheme.error_log.filter_from_errors()
            raise ParsingError("Scheme validation failed. reason: %r"
                               % scheme_errors)

        message_class = getattr(messages, root.tag)
        kwargs = dict([(element.tag, self._decode(element))
                       for element in root.getchildren()])

        return message_class(**kwargs)

    def _encode(self, data):
        """Encode the given data according to its type.

        Warning:
            Do not change the order of the type validation! Some types matches
            more than one type(e.g: bool is also a Number).

        Args:
            data (object): an object to encode.

        Returns:
            object. encoded data, depends on the parser type.

        Raises:
            TypeError: given 'data' couldn't be encoded by this parser.
        """
        if data is None:
            return self._NONE_TYPE

        if isinstance(data, basestring):
            # Strings are surrounded by "" in order to prevent decoding errors.
            # Without "", the string '5' will be wrongly decoded as number 5.
            return '"%s"' % data

        if isinstance(data, bool):
            # objectify identify only lower case (true / false) as bool type
            return str(data).lower()

        if isinstance(data, Number):
            return str(data)

        if isinstance(data, dict):
            return self._encode_dict(data)

        if isinstance(data, (list, tuple)):
            return self._encode_list(data)

        if isinstance(data, type):
            return self._encode_class(data)

        if isinstance(data, models.Model):
            return self._encode_resource_data(data)

        if isinstance(data, BaseResource):
            return self._encode_resource(data)

        raise TypeError("Type %r isn't supported by the parser" % type(data))

    def _encode_resource(self, resource):
        """Encode a resource to an XML string.

        Args:
            resource (BaseResource): resource to encode.

        Returns:
            ElementTree. XML element represent a resource.
        """
        resource_element = builder.E(self._RESOURCE_TYPE)

        type_name = extract_type_path(type(resource))

        type_element = builder.E(TYPE_NAME, self._encode(type_name))
        resource_element.append(type_element)

        data_element = builder.E(DATA_NAME, self._encode(resource.data))
        resource_element.append(data_element)

        return resource_element

    def _encode_resource_data(self, resource_data):
        """Encode resource data to an XML string.

        Args:
            resource_data (ResourceData): resource to encode.

        Returns:
            ElementTree. XML element represent a resource.
        """
        resource_element = builder.E(self._RESOURCE_DATA_TYPE)

        type_name = extract_type_path(type(resource_data))

        type_element = builder.E(TYPE_NAME, self._encode(type_name))
        resource_element.append(type_element)

        properties_element = \
            builder.E(PROPERTIES,
                      self._encode(resource_data.get_fields()))
        resource_element.append(properties_element)

        return resource_element

    def _encode_class(self, data_type):
        """Encode a class to an XML string.

        Args:
            data_type (type): class to encode.

        Returns:
            ElementTree. XML element represent the class.
        """
        class_element = builder.E(self._CLASS_TYPE)
        type_element = builder.E(TYPE_NAME,
                                 self._encode(extract_type_path(data_type)))
        class_element.append(type_element)

        return class_element

    def _encode_dict(self, dict_data):
        """Encode a dictionary to an XML string.

        Args:
            dict_data (dict): dictionary to encode.

        Returns:
            ElementTree. XML element represent a dictionary.

        Raises:
            ParsingError: one of the keys is not of type str.
        """
        dict_element = builder.E(self._DICT_TYPE)

        for key, value in dict_data.iteritems():
            if not isinstance(key, basestring):
                raise ParsingError("Failed to encode dictionary, "
                                   "key %r is not a string" % key)

            element = builder.E(key, self._encode(value))
            dict_element.append(element)

        return dict_element

    def _encode_list(self, list_data):
        """Encode a list to an XML string.

        Args:
            list_data (list): list to encode.

        Returns:
            ElementTree. XML element represent a list.
        """
        list_element = builder.E(self._LIST_TYPE)

        for item in list_data:
            element = builder.E(self._LIST_ITEM_TYPE, self._encode(item))
            list_element.append(element)

        return list_element

    def _decode(self, element):
        """Decode an XML element according to its inner type.

        Args:
            element (ElementTree): an XML element.

        Returns:
            object. decoded object.

        Raises:
            ParsingError: failed to decode the element.
        """
        sub_elements = element.getchildren()

        # If it has no children it is a basic type
        if len(sub_elements) == 0:
            value = element.pyval

            if value == self._NONE_TYPE:
                return None

            # Strings are encoded with "" surrounding them, therefore when
            # decoding a string the "" are removed.
            if isinstance(value, basestring):
                return value[1:-1]

            if isinstance(value, (bool, Number)):
                return value

        # The XML parser's scheme allows only 1 child under each element
        # (unless it is dictionary, list or resource).
        sub_element = sub_elements[0]

        try:
            decoder = self.complex_decoders[sub_element.tag]
            return decoder(sub_element)

        except Exception as exception:
            raise ParsingError("Failed to decode element %r. Reason: %s" %
                               (element, exception))

    def _decode_resource_data(self, resource_element):
        """Decode a resource element.

        Args:
            resource_element (ElementTree): an XML element that represent a
                resource.

        Returns:
            BaseResource. decoded resource.
        """
        type_element = getattr(resource_element, TYPE_NAME)
        type_name = self._decode(type_element)
        resource_type = extract_type(type_name)

        properties_element = getattr(resource_element, PROPERTIES)
        resource_properties = self._decode(properties_element)

        # Get the related fields.
        list_field_names = [key for key, value in resource_properties.items()
                            if isinstance(value, list)]

        list_fields = [(field_name, resource_properties.pop(field_name))
                       for field_name in list_field_names]

        resource = resource_type(**resource_properties)

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
            resource_element (ElementTree): an XML element that represent a
                resource.

        Returns:
            BaseResource. decoded resource.
        """
        type_element = getattr(resource_element, TYPE_NAME)
        type_name = self._decode(type_element)
        resource_type = extract_type(type_name)

        data_element = getattr(resource_element, DATA_NAME)
        resource_data = self._decode(data_element)

        resource = resource_type(data=resource_data)

        return resource

    def _decode_class(self, class_element):
        """Decode a class element.

        Args:
            class_element (ElementTree): an XML element that represent a class.

        Returns:
            type. decoded class.
        """
        type_element = getattr(class_element, TYPE_NAME)
        type_path = self._decode(type_element)
        return extract_type(type_path)

    def _decode_dict(self, dict_element):
        """Decode a dictionary element.

        Args:
            dict_element (ElementTree): an XML element that represent a dict.

        Returns:
            dict. decoded dictionary.
        """
        dictionary = {}
        for element in dict_element.getchildren():
            dictionary[element.tag] = self._decode(element)

        return dictionary

    def _decode_list(self, list_element):
        """Decode a list element.

        Args:
            list_element (ElementTree): an XML element that represent a list.

        Returns:
            list. decoded list.
        """
        return [self._decode(item) for item in list_element.getchildren()]
