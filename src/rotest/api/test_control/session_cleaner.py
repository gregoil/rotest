"""Module for dead sessions cleanup logic."""
from __future__ import absolute_import

import time
from threading import Thread

from rotest.core.models import GeneralData, CaseData
from rotest.core.models.case_data import TestOutcome

from .middleware import SESSIONS


CLEANER_CYCLE = 60  # Seconds


def revalidate_sessions():
    """Go over the sessions and clear dead ones."""
    for session_key in list(SESSIONS.keys()):
        session_data = SESSIONS[session_key]
        if session_data.timeout and session_data.timeout < time.time():
            for test in session_data.all_tests.values():
                if test.status == GeneralData.IN_PROGRESS:
                    if isinstance(test, CaseData):
                        test.update_result(TestOutcome.ERROR,
                                           "Reached session timeout")

                    else:
                        test.end()

                    test.save()

            SESSIONS.pop(session_key)


def run_session_cleaner():
    """Create a thread that revalidates the sessions periodically."""
    def cleaner_main():
        while True:
            revalidate_sessions()
            time.sleep(CLEANER_CYCLE)

    cleaner_thread = Thread(target=cleaner_main)
    cleaner_thread.daemon = True
    cleaner_thread.start()
