from swagapi.api.base_api import (AbstractAPIModel,
                                  NumberField,
                                  StringField, ArrayField, ModelField)


class TestModel(AbstractAPIModel):
    TITLE = "Test"
    PROPERTIES = [
        NumberField(name="id"),
        StringField(name="name"),
        StringField(name="class"),
        ArrayField(name="subfields", items_type="TestModel")
    ]


class EmptyModel(AbstractAPIModel):
    TITLE = "Generic Object"
    PROPERTIES = []
    EXAMPLE = {}


class ResourceDescriptorModel(AbstractAPIModel):
    TITLE = "Resource Descriptor"
    PROPERTIES = [
        StringField(name="type", required=True,
                    example="resources.models.CalculatorData"),
        ModelField(name="properties", model=EmptyModel, required=True),
    ]

    EXAMPLE = {
        "type": "resources.models.CalculatorData",
        "properties": {}
    }


class ChangeResourcePostModel(AbstractAPIModel):
    PROPERTIES = [
        ModelField(name="resource_descriptor", required=True,
                   model=ResourceDescriptorModel),
        ModelField(name="changes", required=True, model=EmptyModel)
    ]


class DescribedResourcesPostModel(AbstractAPIModel):
    PROPERTIES = [
        ArrayField(name="descriptors", items_type=ResourceDescriptorModel,
                   required=True),
        NumberField(name="timeout", required=True)
    ]


class ResourcesModel(AbstractAPIModel):
    PROPERTIES = [
        ArrayField(name="resources", items_type=StringField("resource_name"),
                   example=["calc1", "calc2"], required=True)
    ]
    EXAMPLE = {
        "resources": ["calc1", "calc2"]
    }
