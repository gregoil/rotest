SESSIONS = {}


def session_middleware(get_response):
    def middleware(request, *args, **kwargs):
        return get_response(request, sessions=SESSIONS, *args, **kwargs)

    return middleware
