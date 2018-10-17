"""Define SuiteData model class."""
# pylint: disable=no-init,old-style-class
from future.builtins import object

from .general_data import GeneralData


class SuiteData(GeneralData):
    """Contain information about a TestSuite run.

    Attributes:
        tests (list): list of contained test datas, generated as a result
            of the foreign key 'parent' defined in
            :class:`rotest.core.models.general_data.GeneralData`.
    """
    class Meta(object):
        """Define the Django application for this model."""
        app_label = 'core'

    def add_sub_test_data(self, sub_test_data):
        """Add the sub test data as a child.

        Args:
            sub_test_data (GeneralData): sub test data to add.
        """
        sub_test_data.parent = self
