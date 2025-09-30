from typing import List
from anytree import NodeMixin


class NodeIOTypes:
    BINARY = "binary"
    FLOAT = "float"


class Node(NodeMixin):
    def __init__(
        self,
        input_types: List[NodeIOTypes],
        output_type: NodeIOTypes,
        max_childs: int,
    ):
        self.max_childs = max_childs
        self.input_types = input_types
        self.output_type = output_type
        self.childs = []

    def __repr__(self):
        return self.name

    def __call__(self, *inputs):
        return self.activate(*inputs)

    @property
    def name(self):
        return type(self).__name__ + "()"

    @property
    def full(self):
        return len(self.childs) >= self.max_childs

    def add_child(self, child: NodeMixin):
        child.set_parent(self)
        self.childs.append(child)

    def set_parent(self, parent):
        self.parent = parent

    def activate(self, *inputs):
        raise NotImplementedError

    def propagate(self):
        if not self.full:
            raise ValueError("can't propagate through this node if not node.full")
        return self.activate(*[c.propagate() for c in self.childs])
