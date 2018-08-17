from swaggapi.api.builder.common.fields import (NumberField,
                                                StringField,
                                                ArrayField,
                                                ModelField,
                                                DynamicType, BoolField)
from swaggapi.api.builder.common.model import AbstractAPIModel


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


class TestResultModel(AbstractAPIModel):
    PROPERTIES = [
        NumberField(name="result_code", required=True),
        StringField(name="info", required=True)
    ]
    EXAMPLE = {
        "result_code": 100,
        "info": "test failed to finish correctly"
    }


class TestOperation(AbstractAPIModel):
    PROPERTIES = [
        StringField(name="token", required=True),
        NumberField(name="test_id", required=True)
    ]
    EXAMPLE = {
        "token": "token",
        "test_id": 0
    }


class UpdateResourcesModel(AbstractAPIModel):
    PROPERTIES = [
        ArrayField(name="descriptors", items_type=ResourceDescriptorModel,
                   required=True),
        ModelField(name="test_details", model=TestOperation, required=True)
    ]


class AddTestResultModel(AbstractAPIModel):
    PROPERTIES = [
        ModelField(name="test_details", model=TestOperation, required=True),
        ModelField(name="result", model=TestResultModel, required=True)
    ]


class TestModel(AbstractAPIModel):
    TITLE = "Test"
    PROPERTIES = [
        NumberField(name="id"),
        StringField(name="name"),
        StringField(name="class"),
        ArrayField(name="subtests",
                   items_type=DynamicType("TestModel",
                                          "rotest.api.common.models"))
    ]


class RunDataModel(AbstractAPIModel):
    TITLE = "RunData"
    PROPERTIES = [
        StringField(name="run_name"),
        StringField(name="artifact_path"),
        BoolField(name="run_delta"),
        StringField(name="user_name")
    ]


class UpdateRunDataModel(AbstractAPIModel):
    PROPERTIES = [
        ModelField(name="run_data", model=RunDataModel, required=True),
        StringField(name="token", required=True)
    ]


class StartTestRunModel(AbstractAPIModel):
    PROPERTIES = [
        ModelField(name="tests", model=TestModel, required=True),
        ModelField(name="run_data", model=RunDataModel, required=True)
    ]
