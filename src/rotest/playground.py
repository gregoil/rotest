from __future__ import absolute_import
from rotest import main
from rotest.core.block import TestBlock
from rotest.core.flow import TestFlow


class ABlock(TestBlock):
    def test_method(self):
        pass


class AFlow(TestFlow):
    blocks = [
        ABlock
    ]

if __name__ == '__main__':
    main(AFlow)
