"""Parameters models of the view requests."""
from __future__ import absolute_import
from swaggapi.api.builder.common.model import AbstractAPIModel
from swaggapi.api.builder.common.fields import (NumberField,
                                                StringField,
                                                DynamicType,
                                                ArrayField,
                                                ModelField,
                                                BoolField)


class GenericModel(AbstractAPIModel):
    """Generic model can be any dict object."""
    TITLE = "Generic Object"
    PROPERTIES = []


class TokenModel(AbstractAPIModel):
    """Model that contains only a session token."""
    PROPERTIES = [
        StringField(name="token", required=True)
    ]


class ResourceDescriptorModel(AbstractAPIModel):
    """Descriptor of a resource.

    Args:
        type (str): the type of the resource.
        properties (dict): django filter properties of the model.
    """
    TITLE = "Resource Descriptor"
    PROPERTIES = [
        StringField(name="type", required=True,
                    example="resources.models.CalculatorData"),
        ModelField(name="properties", model=GenericModel, required=True)
    ]


class UpdateFieldsParamsModel(AbstractAPIModel):
    """Update fields of a given resource.

    Args:
        resource_descriptor (ResourceDescriptorModel): describes the
            resources to change.
        changes (dict): keys are the object's fields and values are the
            values to change the fields into.
    """
    PROPERTIES = [
        ModelField(name="resource_descriptor", required=True,
                   model=ResourceDescriptorModel),
        ModelField(name="changes", required=True, model=GenericModel),
    ]


class LockResourcesParamsModel(AbstractAPIModel):
    """Lock the given described resources.

    Args:
        descriptors (list): list of ResourceDescriptorModel - the required
            resource to be locked.
    """
    PROPERTIES = [
        ArrayField(name="descriptors", items_type=ResourceDescriptorModel,
                   required=True),
        StringField(name="token", required=True)
    ]


class ReleaseResourcesParamsModel(AbstractAPIModel):
    """Release the given resources names.

    Args:
        resources (list): list of str. resource names to be released.
    """
    PROPERTIES = [
        ArrayField(name="resources", items_type=StringField("resource_name"),
                   example=["calc1", "calc2"], required=True),
        StringField(name="token", required=True)
    ]


class TestResultModel(AbstractAPIModel):
    """Describes the result of a test.

    Args:
        result_code (number): the end result code of the test.
        info (str): additional info of the test run.
    """
    PROPERTIES = [
        NumberField(name="result_code", required=True),
        StringField(name="info", required=True)
    ]


class TestControlOperationParamsModel(AbstractAPIModel):
    """Generic data structure of test control operations.

    Args:
        token (str): the session token of the current test run.
        test_id (number): the relevant test to be influenced by the operation.
    """
    PROPERTIES = [
        StringField(name="token", required=True, location="query"),
        NumberField(name="test_id", required=True, location="query")
    ]


class SetSessionTimeoutModel(AbstractAPIModel):
    """Set a timeout to the session, override the previous one.

    Args:
        token (str): the session token of the current test run.
        timeout (number): timeout to set to the session.
    """
    PROPERTIES = [
        StringField(name="token", required=True, location="query"),
        NumberField(name="timeout", required=True, location="query")
    ]


class UpdateResourcesParamsModel(AbstractAPIModel):
    """Update the given resources test data.

    Args:
        descriptors (list): list of ResourceDescriptorModel.
            The resources to be updated.
        test_details (TestControlOperationParamsModel): the details of the
            relevant session datas.
    """
    PROPERTIES = [
        ArrayField(name="descriptors", items_type=ResourceDescriptorModel,
                   required=True),
        ModelField(name="test_details",
                   model=TestControlOperationParamsModel, required=True,
                   location="query")
    ]


class AddTestResultParamsModel(AbstractAPIModel):
    """Add a test result to a given test.

    Args:
        test_details (TestControlOperationParamsModel): the details of the
            relevant session datas.
        result (TestResultModel): the result of the test.
    """
    PROPERTIES = [
        ModelField(name="test_details",
                   model=TestControlOperationParamsModel, required=True,
                   location="query"),
        ModelField(name="result", model=TestResultModel, required=True)
    ]


class TestModel(AbstractAPIModel):
    """Test model structure.

    Args:
        id (number): the id of the test.
        name (str): the name of the test.
        class (str): the classname of the test.
        subtests (list): list of TestModel. Sub-tests of the current test.
    """
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
    """Run data model structure."""
    TITLE = "RunData"
    PROPERTIES = [
        StringField(name="run_name"),
        StringField(name="artifact_path"),
        BoolField(name="run_delta"),
        StringField(name="user_name"),
        StringField(name="config"),
    ]


class UpdateRunDataParamsModel(AbstractAPIModel):
    """Update run data of a given session run.

    Args:
        run_data (RunDataModel): the new run data to update to.
        token (str): the token of the current session run.
    """
    PROPERTIES = [
        ModelField(name="run_data", model=RunDataModel, required=True),
        StringField(name="token", required=True)
    ]


class StartTestRunParamsModel(AbstractAPIModel):
    """Start a new run session.

    Args:
        tests (TestModel): the main test to build the run suite from.
        run_data (RunDataModel): the run data details of the current run.
    """
    PROPERTIES = [
        StringField(name="token", required=True),
        ModelField(name="tests", model=TestModel, required=True),
        ModelField(name="run_data", model=RunDataModel, required=True)
    ]


class SignatureControlParamsModel(AbstractAPIModel):
    """Model structure of signature control operation.

    Args:
        error (str): error message.
    """
    PROPERTIES = [
        StringField(name="error", required=True),
    ]
