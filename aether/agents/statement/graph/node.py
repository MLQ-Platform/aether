from typing import List
from aether.agents.statement.graph.types import NodeType


class Node:
    """
    Statement Graph Node
    """

    def __init__(
        self,
        text: str,
        node_id: str,
        node_type: NodeType,
        version: int = 0,
        confidence: float = 1.0,
    ):
        self.text = text
        self.node_id = node_id
        self.node_type = node_type
        self.version = version
        self.confidence = confidence
        self.edges: List[str] = []

    def add_edge(self, target_node_id: str):
        if target_node_id not in self.edges:
            self.edges.append(target_node_id)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "text": self.text,
            "version": self.version,
            "confidence": self.confidence,
            "edges": self.edges,
        }
