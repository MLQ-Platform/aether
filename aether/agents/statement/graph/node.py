from typing import Any
from typing import List
from typing import Optional
from aether.agents.rationale.schema import Rationale
from aether.agents.statement.graph.types import NodeType
from aether.utils import generate_uuid


class Node:
    """
    Statement Graph Node
    """

    def __init__(
        self,
        instance: str,
        node_type: NodeType,
        node_id: Optional[int] = None,
    ):
        self.instance = instance
        self.node_id = node_id or generate_uuid()
        self.node_type = node_type
        self.edges: List[int] = []

    def add_edge(self, target_node_id: Any):
        if target_node_id not in self.edges:
            self.edges.append(target_node_id)

    def __repr__(self) -> str:
        return f"Node(node_id={self.node_id}, node_type={self.node_type})"
