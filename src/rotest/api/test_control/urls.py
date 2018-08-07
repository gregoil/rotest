from django.conf.urls import url, patterns

from rotest.api.test_control.middleware import SessionMiddleware
from rotest.api.test_control.views.stop_test import stop_test
from rotest.api.test_control.views.start_test import start_test
from rotest.api.test_control.views.should_skip import should_skip
from rotest.api.test_control.views.start_test_run import start_test_run
from rotest.api.test_control.views.stop_composite import stop_composite
from rotest.api.test_control.views.start_composite import start_composite
from rotest.api.test_control.views.update_run_data import update_run_data
from rotest.api.test_control.views.add_test_result import add_test_result

urlpatterns = patterns("",
    url("^start_test/?", SessionMiddleware(start_test)),
    url("^stop_tests/?", SessionMiddleware(stop_test)),
    url("^start_test_run/?", SessionMiddleware(start_test_run)),
    url("^should_skip/?", SessionMiddleware(should_skip)),
    url("^start_composite/?", SessionMiddleware(start_composite)),
    url("^stop_composite/?", SessionMiddleware(stop_composite)),
    url("^update_run_data/?", SessionMiddleware(update_run_data)),
    url("^add_test_result/?", SessionMiddleware(add_test_result)),
)
