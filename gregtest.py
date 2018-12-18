from rotest.core import TestBlock, TestFlow
import ipdbugger

class Block1(TestBlock):
    def test_method(self):
        pass

class Block2(TestBlock):
    def test_method(self):
        raise RuntimeError("greggggggggg")

class Block3(TestBlock):
    def test_method(self):
        import ipdb; ipdb.set_trace()
        self.parent.jump_to(2)

class SubFlow(TestFlow):
    __test__ = False
    blocks = [Block1, Block2, Block1]

class TopFlow(TestFlow):
    blocks = [Block3, Block1, SubFlow, Block1]
