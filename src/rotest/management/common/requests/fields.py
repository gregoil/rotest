from rotest.management.common.requests.base_api import (AbstractField,
                                                        AbstractAPIArray,
                                                        AbstractAPIModel)


class TokenField(AbstractField):
    """token generated using start_run_test"""
    NAME = "token"
    TYPE = "string"


class TestIDField(AbstractField):
    NAME = "test_id"
    TYPE = "integer"


class TestField(AbstractField):
    NAME = "tests"
    TYPE = AbstractAPIModel


class IDField(AbstractField):
    NAME = "id"
    TYPE = "integer"


class NameField(AbstractField):
    NAME = "name"
    TYPE = "string"


class ClassField(AbstractField):
    NAME = "class"
    TYPE = "string"


class TypeField(AbstractField):
    NAME = "type"
    TYPE = "string"


class PropertiesField(AbstractField):
    NAME = "properties"
    TYPE = "object"


class SubTestsField(AbstractAPIArray):
    NAME = "subfields"
    ITEMS_TYPE = "TestModel"


class TestModel(AbstractAPIModel):
    TITLE = "Test"
    PROPERTIES = [
        IDField,
        NameField,
        ClassField,
        SubTestsField
    ]


class ResourceDescriptorModel(AbstractAPIModel):
    TITLE = "Resource Descriptor"
    PROPERTIES = [
        TypeField,
        PropertiesField,
    ]


class DescriptorsField(AbstractAPIArray):
    """descriptors of the tests"""
    NAME = "descriptors"
    ITEMS_TYPE = "ResourceDescriptorModel"


class ResourcesField(AbstractField):
    NAME = "resources"
    TYPE = "object"
