import os
import sys

import delegator


def test_sanity():
    playground = os.path.join("tests", "integration", "playground.py")
    process = delegator.run("{python} {playground}"
                            .format(python=sys.executable,
                                    playground=playground),
                            env={"DJANGO_SETTING_MODULE":
                                 "rotest.common.django_utils.settings"})

    process.block()
    assert "Test run has started" in process.err
    assert 'ExampleBlock1 ran' in process.out
    assert 'ExampleBlock2 ran' in process.out
    assert process.ok
