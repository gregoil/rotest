from django.conf.urls import include, url
urlpatterns = [
    url("^lock_resources/?", None),
    url("^release_resources/?", None),
    url("^query_resources/?", None),
    url("^cleanup_user/?", None),
]