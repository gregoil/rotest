import sys

import delegator


def test_sanity():
    process = delegator.run("{python} "
                            "tests/integration/playground.py"
                            .format(python=sys.executable),
                            env={"DJANGO_SETTING_MODULE":
                                     "rotest.common.django_utils.settings"})

    process.block()
    assert("Test run has started" in process.err)
    assert('ExampleBlock1 ran' in process.out)
    assert('ExampleBlock2 ran' in process.out)
    assert(process.ok)
