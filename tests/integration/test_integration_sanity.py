import os
import sys

import subprocess

THIS_FILE = os.path.abspath(__file__)


def test_sanity():
    python = sys.executable
    playground = os.path.join(os.path.dirname(THIS_FILE), "playground.py")
    environment_variables = {
        "DJANGO_SETTINGS_MODULE":
            "rotest.common.django_utils.settings"
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
