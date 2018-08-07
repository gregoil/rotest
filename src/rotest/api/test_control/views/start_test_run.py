import httplib
from uuid import UUID

from django.http import JsonResponse

from rotest.api.constants import \
    RESPONSE_PAGE_NOT_IMPLEMENTED
from rotest.api.test_control.views.session_data import SessionData
from rotest.core.models import RunData


TEST_ID_KEY = 'id'
TEST_NAME_KEY = 'name'
TEST_CLASS_CODE_KEY = 'class'
TEST_SUBTESTS_KEY = 'subtests'


def _create_test_data(test_dict, run_data, all_tests):
    """Recursively create the test's datas and add them to 'all_tests'.

    Args:
        tests_tree (dict): contains the hierarchy of the tests in the run.

    Returns:
        GeneralData. the created test data object.
    """
    data_type = test_dict[TEST_CLASS_CODE_KEY]
    test_data = data_type(name=test_dict[TEST_NAME_KEY])
    test_data.run_data = run_data
    test_data.save()
    all_tests[test_dict[TEST_ID_KEY]] = test_data

    if TEST_SUBTESTS_KEY in test_dict:
        for sub_test_dict in test_dict[TEST_SUBTESTS_KEY]:
            sub_test = _create_test_data(sub_test_dict,
                                         run_data,
                                         all_tests)
            test_data.add_sub_test_data(sub_test)
            sub_test.save()

    return test_data


def start_test_run(request, sessions=None, *args, **kwargs):
    """Initialize the tests run data.

    Args:
        tests_tree (dict): contains the hierarchy of the tests in the run.
        run_data (dict): contains additional data about the run.
    """
    if request.method != "POST":
        return JsonResponse(RESPONSE_PAGE_NOT_IMPLEMENTED,
                            status=httplib.BAD_REQUEST)

    run_data = RunData.objects.create(**request.POST.get("rundata"))
    all_tests = {}
    tests_tree = request.POST.get("tests")
    main_test = _create_test_data(tests_tree, run_data, all_tests)
    run_data.main_test = main_test
    run_data.user_name = request.get_host()
    run_data.save()

    session_token = UUID()
    sessions[session_token] = SessionData(all_tests=all_tests,
                                          run_data=run_data,
                                          main_test=main_test,
                                          user_name=run_data.user_name)
    response = {
        "token": session_token
    }
    return JsonResponse(response, status=httplib.NO_CONTENT)
