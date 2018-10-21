import os
import sys

import delegator


THIS_FILE = os.path.abspath(__file__)


def test_sanity():
    playground = os.path.join(os.path.dirname(THIS_FILE), "playground.py")
    process = delegator.run("{python} {playground}"
                            .format(python=sys.executable,
                                    playground=playground),
                            env={"DJANGO_SETTINGS_MODULE":
                                 "rotest.common.django_utils.settings"})

    process.block()
    assert "Test run has started" in process.err
    assert 'ExampleBlock1 ran' in process.out
    assert 'ExampleBlock2 ran' in process.out
    assert process.ok
