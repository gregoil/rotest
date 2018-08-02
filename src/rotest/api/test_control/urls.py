from django.conf.urls import include, url

urlpatterns = [
    url("^start_test/?", None),
    url("^stop_tests/?", None),
    url("^start_test_run/?", None),
    url("^should_skip/?", None),
    url("^start_composite/?", None),
    url("^stop_composite/?", None),
    url("^update_run_data/?", None),
    url("^add_test_result/?", None),
    url("^add_result/?", None),
]
