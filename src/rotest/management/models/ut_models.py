"""Define Rotest UT model classes."""
# pylint: disable=attribute-defined-outside-init
# pylint: disable=too-many-public-methods,old-style-class
# pylint: disable=no-self-use,no-init,no-member,too-few-public-methods
import os
import shutil

from django.db import models

from rotest.management.base_resource import BaseResource
from rotest.management.models.resource_data import ResourceData


class DemoResourceData(ResourceData):
    """Fake resource class, used in resource manager tests.

    Attributes:
        version (number): version identifier.
        ip_address (str): ip address identifier.
        mode (number): mode identifier (boot/ production).

        reset_flag (bool): tells if the resource was reset.
        validate_flag (bool): tells if the resource was validated.
        finalization_flag (bool): tells if the resource was finalized.
        initialization_flag (bool): tells if the resource was initialized.

        fails_on_finalize (bool): the resource should fail on finalization.
        fails_on_initialize (bool): the resource should fail on initialization.
    """
    BOOT_MODE, PROD_MODE = xrange(2)

    MODE_CHOICE = ((BOOT_MODE, 'Boot'),
                   (PROD_MODE, 'Production'))

    version = models.PositiveSmallIntegerField()
    ip_address = models.IPAddressField()
    mode = models.IntegerField(choices=MODE_CHOICE, default=BOOT_MODE)

    validation_result = models.BooleanField(default=False)
    reset_flag = models.BooleanField(default=False)
    validate_flag = models.NullBooleanField(default=False)
    finalization_flag = models.BooleanField(default=False)
    initialization_flag = models.BooleanField(default=False)

    fails_on_finalize = models.BooleanField(default=False)
    fails_on_initialize = models.BooleanField(default=False)

    class Meta:
        """Define the Django application for this model."""
        app_label = 'management'


class DemoResource(BaseResource):
    """Fake resource class, used in resource manager tests."""
    DATA_CLASS = DemoResourceData
    STATE_FILE_NAME = 'state.bin'

    def store_state(self, state_dir_path):
        """Save a fake state file under the state directory."""
        state_file_path = os.path.join(state_dir_path, self.STATE_FILE_NAME)
        with open(state_file_path, 'wb') as state_file:
            state_file.write('state')

    def initialize(self):
        """Turns on the initialization flag and calls 'boot_mode' method."""
        if self.data.fails_on_initialize:
            raise RuntimeError("Intentional Error in initialization")

        self.data.initialization_flag = True
        self.data.save()
        self.boot_mode()

    def set_work_dir(self, logical_name, case_work_dir):
        """Set the resource work directory."""

        # Because of Django unit-test DB fixture loading mechanism, cases
        # primary key are duplicated when the a new fixture is loaded, thus
        # work_dir names are also duplicated. this is a fix to this phenomena.
        work_dir_path = os.path.join(case_work_dir, logical_name)
        if os.path.exists(work_dir_path):
            shutil.rmtree(work_dir_path)

        super(DemoResource, self).set_work_dir(logical_name, case_work_dir)

    def boot_mode(self):
        """Change resource data mode value."""
        self.data.mode = DemoResourceData.BOOT_MODE
        self.data.save()

    def production_mode(self):
        """Change resource data mode value."""
        self.data.mode = DemoResourceData.PROD_MODE
        self.data.save()

    def process_data(self, input_string):
        """Convert input string case into lower / upper according to version.

        Returns:
            str: lower/upper case version of the input_string

        Raises:
            RuntimeError: In case the resource mode is not 'production'
        """
        if self.data.mode is not DemoResourceData.PROD_MODE:
            raise RuntimeError("Invalid mode, resource [%s] can't process data"
                " while in mode [%s]" % (self.name, self.data.mode))

        if self.data.version <= 2:
            return input_string.lower()

        return input_string.upper()

    def finalize(self):
        """Turns on the finalization flag."""
        if self.data.fails_on_finalize:
            raise RuntimeError("Intentional Error in finalization")

        self.data.finalization_flag = True
        self.data.save()

    def validate(self):
        """Change validation flag.

        Returns:
            bool. validation of resource.
        """
        self.data.validate_flag = True
        self.data.save()
        return self.data.validation_result

    def reset(self):
        """Set flag to True once the resource is reseted."""
        self.data.reset_flag = True
        self.data.save()


class DemoComplexResourceData(ResourceData):
    """Fake complex resource class, used in resource manager tests.

    Attributes:
        reset_flag (bool): tells if the resource was reset.
        validate_flag (bool): tells if the resource was validated.
        finalization_flag (bool): tells if the resource was finalized.
        initialization_flag (bool): tells if the resource was initialized.
        demo1 (DemoResourceData): sub resource data pointer.
        demo2 (DemoResourceData): sub resource data pointer.
    """
    reset_flag = models.BooleanField(default=False)
    validate_flag = models.NullBooleanField(default=None)
    finalization_flag = models.BooleanField(default=False)
    initialization_flag = models.BooleanField(default=False)

    demo1 = models.ForeignKey(DemoResourceData, related_name="demo_resource1")
    demo2 = models.ForeignKey(DemoResourceData, related_name="demo_resource2")

    class Meta:
        """Define the Django application for this model."""
        app_label = 'management'


class DemoComplexResource(BaseResource):
    """Fake complex resource class, used in resource manager tests.

    Attributes:
        demo1 (DemoResource): sub resource pointer.
        demo2 (DemoResource): sub resource pointer.
    """
    DATA_CLASS = DemoComplexResourceData

    def create_sub_resources(self):
        """Return an iterable to the complex resource's sub-resources."""
        self.demo1 = DemoResource(data=self.data.demo1)
        self.demo2 = DemoResource(data=self.data.demo2)
        return (self.demo1, self.demo2)

    def initialize(self):
        """Turns on the initialization flag."""
        super(DemoComplexResource, self).initialize()
        self.data.initialization_flag = True
        self.data.save()

    def finalize(self):
        """Turns on the finalization flag."""
        self.finalization_flag = True
        self.save()
        super(DemoComplexResource, self).finalize()

    def validate(self):
        """Change validation flag.

        Returns:
            bool. validation of resource.
        """
        super(DemoComplexResource, self).validate()

        self.data.validate_flag = True
        self.data.save()
        return False

    def reset(self):
        """Set flag to True once the resource is reseted."""
        self.data.reset_flag = True
        self.data.save()


class NonExistingResource(BaseResource):
    """Fake resource class, used in tests as a missing resource."""
    DATA_CLASS = ResourceData


class InitializationError(StandardError):
    """Will be thrown intentionally on connect."""
    pass


class InitializeErrorResource(DemoResource):
    """Resource that raises an exception when initialize is called."""
    def initialize(self):
        """Raise an exception."""
        raise InitializationError("Intentional error in initialize")


class DemoService(BaseResource):
    """Fake service class, used in resource manager tests."""
    DATA_CLASS = None
