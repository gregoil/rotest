import os
import sys

import subprocess

THIS_FILE = os.path.abspath(__file__)
THIS_DIRECTORY = os.path.dirname(THIS_FILE)
ROTEST_WORK_DIR = os.path.join(os.path.expanduser("~"), ".rotest")


def test_sanity():
    python = sys.executable
    playground = os.path.join(THIS_DIRECTORY, "playground.py")
    environment_variables = {
        "DJANGO_SETTINGS_MODULE":
            "rotest.common.django_utils.settings",
        "ROTEST_WORK_DIR": ROTEST_WORK_DIR
    }

    p = subprocess.Popen([python, playground], env=environment_variables,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return_code = p.wait()
    stderr = p.stderr.read()
    stdout = p.stdout.read()
    assert b"Test run has started" in stderr
    assert b'ExampleBlock1 ran' in stdout
    assert b'ExampleBlock2 ran' in stdout
    assert return_code == 0
