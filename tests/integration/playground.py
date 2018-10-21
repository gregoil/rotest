from __future__ import absolute_import, print_function

from rotest import main
from rotest.core import TestBlock, TestFlow


class ExampleBlock1(TestBlock):
    __test__ = False

    def test_method(self):
        print("ExampleBlock1 ran")


class ExampleBlock2(TestBlock):
    __test__ = False

    def test_method(self):
        print("ExampleBlock2 ran")


class ExampleFlow(TestFlow):
    __test__ = False

    blocks = [
        ExampleBlock1,
        ExampleBlock2
    ]


if __name__ == "__main__":
    main(ExampleFlow)
