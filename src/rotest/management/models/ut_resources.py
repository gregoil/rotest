"""Demo resources for ut."""
# pylint: disable=attribute-defined-outside-init
from __future__ import absolute_import

import os
import shutil

from rotest.management.base_resource import BaseResource
from .ut_models import ResourceData, DemoResourceData, DemoComplexResourceData


class DemoResource(BaseResource):
    """Fake resource class, used in resource manager tests."""
    DATA_CLASS = DemoResourceData
    STATE_FILE_NAME = 'state.bin'

    def store_state(self, state_dir_path):
        """Save a fake state file under the state directory."""
        state_file_path = os.path.join(state_dir_path, self.STATE_FILE_NAME)
        with open(state_file_path, 'w') as state_file:
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
        self.data.finalization_flag = True
        self.data.save()
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


class InitializationError(Exception):
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
