class SessionMiddleware(object):
    SESSIONS = {}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request, *args, **kwargs):
        return self.get_response(request, sessions=self.SESSIONS,
                                 *args, **kwargs)
