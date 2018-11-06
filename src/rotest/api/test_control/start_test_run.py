# pylint: disable=unused-argument, no-self-use
from __future__ import absolute_import

from six.moves import http_client
from swaggapi.api.builder.server.response import Response
from swaggapi.api.builder.server.exceptions import BadRequest
from swaggapi.api.builder.server.request import DjangoRequestView

from rotest.core.models import RunData
from rotest.management.common.parsers import JSONParser
from rotest.api.common.models import StartTestRunParamsModel
from rotest.api.test_control.middleware import session_middleware
from rotest.api.common.responses import (SuccessResponse,
                                         FailureResponseModel)


TEST_ID_KEY = 'id'
TEST_NAME_KEY = 'name'
TEST_CLASS_CODE_KEY = 'class'
TEST_SUBTESTS_KEY = 'subtests'


class StartTestRun(DjangoRequestView):
    """Initialize the tests run data.

    Args:
        tests_tree (dict): contains the hierarchy of the tests in the run.
        run_data (dict): contains additional data about the run.
    """
    URI = "tests/start_test_run"
    DEFAULT_MODEL = StartTestRunParamsModel
    DEFAULT_RESPONSES = {
        http_client.NO_CONTENT: SuccessResponse,
        http_client.BAD_REQUEST: FailureResponseModel
    }
    TAGS = {
        "post": ["Tests"]
    }

    def _create_test_data(self, test_dict, run_data, all_tests):
        """Recursively create the test's datas and add them to 'all_tests'.

        Args:
            tests_tree (dict): contains the hierarchy of the tests in the run.

        Returns:
            GeneralData. the created test data object.
        """
        parser = JSONParser()
        data_type = parser.recursive_decode(test_dict[TEST_CLASS_CODE_KEY])
        try:
            test_data = data_type(name=test_dict[TEST_NAME_KEY])

        except TypeError:
            raise BadRequest("Invalid type provided: {}".format(data_type))

        test_data.run_data = run_data
        test_data.save()
        all_tests[test_dict[TEST_ID_KEY]] = test_data

        if TEST_SUBTESTS_KEY in test_dict:
            for sub_test_dict in test_dict[TEST_SUBTESTS_KEY]:
                sub_test = self._create_test_data(sub_test_dict,
                                                  run_data,
                                                  all_tests)
                test_data.add_sub_test_data(sub_test)
                sub_test.save()

        return test_data

    @session_middleware
    def post(self, request, sessions, *args, **kwargs):
        """Initialize the tests run data.

        Args:
            tests_tree (dict): contains the hierarchy of the tests in the run.
            run_data (dict): contains additional data about the run.
        """
        try:
            run_data = RunData.objects.create(**request.model.run_data)

        except TypeError:
            raise BadRequest("Invalid run data provided!")

        all_tests = {}
        tests_tree = request.model.tests
        try:
            main_test = self._create_test_data(tests_tree, run_data, all_tests)

        except KeyError:
            raise BadRequest("Invalid tests tree provided!")

        run_data.main_test = main_test
        run_data.user_name = request.get_host()
        run_data.save()

        session = sessions[request.model.token]
        session.all_tests = all_tests
        session.run_data = run_data
        session.main_test = main_test

        return Response({}, status=http_client.NO_CONTENT)
