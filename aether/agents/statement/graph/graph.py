from typing import Dict
from typing import Optional
from aether.agents.statement.graph.node import Node
from aether.agents.statement.graph.types import NodeType


class StatementGraph:
    """
    Statement Graph
    """

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.concept_id: Optional[str] = None

    def add_node(self, node: Node):
        """
        Add a node to the graph
        """
        self.nodes[node.node_id] = node

        if node.node_type == NodeType.CONCEPT:
            self.concept_id = node.node_id

    def add_edge(self, from_id: str, to_id: str):
        """
        Add an edge to the graph
        """
        if from_id in self.nodes and to_id in self.nodes:
            self.nodes[from_id].add_edge(to_id)

    def display_graph(self):
        """
        Display the graph
        """
        for nid, node in self.nodes.items():
            print(
                f"{nid} [{node.node_type} v{node.version} conf={node.confidence}] -> {node.edges}"
            )
