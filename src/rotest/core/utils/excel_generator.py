"""Excel result file generator script for Rotest projects."""
# pylint: disable=invalid-name,protected-access
from __future__ import absolute_import

import os
import argparse

import django
from future.builtins import object

from rotest.core.models.run_data import RunData
from rotest.common.django_utils import get_sub_model
from rotest.core.models.case_data import CaseData, TestOutcome
from rotest.core.result.handlers.excel_handler import ExcelHandler


class TestSimulator(object):
    """A class that simulates a test or container instance."""
    def __init__(self, data, identifier, parents_count):
        self.data = data
        self.identifier = identifier
        self.parents_count = parents_count
        self.sub_tests = []
        self.IS_COMPLEX = False
        self.__doc__ = None  # don't show class doc in the excel.

    def __iter__(self):
        return iter(self.sub_tests)

    def iter_cases(self):
        """Recursively find and yield the cases of the component.

        Yields:
            CaseData. leaves of the tests tree.
        """
        if not self.IS_COMPLEX:
            yield self

        else:
            for sub_component in self:
                for case in sub_component.iter_cases():
                    yield case


def _generate_tests_tree_by_data(test_data, parents_count=0):
    """Recursively create a pseudo-test item of the test data object.

    Args:
        test_data (GeneralData): test data object.
        parents_count (int): depth in the recurssion.

    Returns:
        TestSimulator. pseudo-test item representing the original test.
    """
    simulator = TestSimulator(data=test_data,
                              identifier=test_data.pk,
                              parents_count=parents_count)

    if not isinstance(test_data, CaseData):
        simulator.IS_COMPLEX = True

        for sub_test in test_data.get_sub_tests_data():
            sub_tree = _generate_tests_tree_by_data(sub_test,
                                                    parents_count + 1)
            simulator.sub_tests.append(sub_tree)

    else:
        simulator.IS_COMPLEX = False
        if (test_data.exception_type != TestOutcome.SUCCESS and
            test_data.should_skip(test_data.name, test_data.run_data)):

            test_data.traceback = ""
            test_data.success = True
            test_data.exception_type = TestOutcome.SUCCESS

    return simulator


def _generate_tests_tree_by_run_name(run_name):
    """Create a pseudo-test item summarizing the tests of the run name.

    Note:
        The summary assumes the last run contained all the relevant tests,
        tests not shown on the last run are not included.

    Args:
        run_name (str): name of the run to summarize.

    Returns:
        TestSimulator. pseudo-test item representing the original test tree.
    """
    run_datas = RunData.objects.filter(run_name=run_name,
                   main_test__isnull=False).order_by('main_test__start_time')

    if not run_datas.exists():
        raise RuntimeError("No runs found for run name %r" % run_name)

    last_run = run_datas.last()
    actual_main_test = get_sub_model(last_run.main_test)
    return _generate_tests_tree_by_data(actual_main_test)


def generate_excel(run_name, dest_path):
    """Create an excel file summarizing the results of the run name.

    Note:
        The summary assumes the last run contained all the relevant tests,
        tests not shown on the last run are not included.

    Args:
        run_name (str): name of the run to summarize.
        dest_path (str): path to create the excel in.
    """
    main_test = _generate_tests_tree_by_run_name(run_name)
    handler = ExcelHandler(main_test, output_file_path=dest_path)
    handler.start_test_run()
    for case in main_test.iter_cases():
        result_type = case.data.exception_type
        if result_type is not None:
            handler._write_case_result(case)

    handler.workbook.save(handler.output_file_path)


def main():
    """Generate an  Excel result file."""
    django.setup()
    parser = argparse.ArgumentParser()

    parser.add_argument("-n", dest="run_name", help="requested run name")
    parser.add_argument("-o", dest="output_path", default=os.path.curdir,
                        help="output Excel file path")
    args = parser.parse_args()

    generate_excel(args.run_name, args.output_path)


if __name__ == '__main__':
    main()
