import json
from pathlib import Path
from typing import Dict
from typing import List
from aether.agents.claim.schema import Claim
from aether.agents.rationale.schema import Rationale
from aether.agents.statement.graph.node import Node
from aether.logger import get_logger

logger = get_logger(__name__)


class StatementGraph:
    """
    Statement Graph
    """

    def __init__(self):
        self.nodes: Dict[int, Node] = {}

    def add_nodes(self, nodes: List[Node]):
        """
        Add multiple nodes to the graph
        """
        for node in nodes:
            self.add_node(node)

    def add_node(self, node: Node):
        """
        Add a node to the graph
        """
        self.nodes[node.node_id] = node

    def add_edge(self, from_id: int, to_id: int):
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
            print(f"Node ID: {nid}")
            print(f"  Type: {node.node_type}")
            if node.edges:
                print(f"  Connected to: {', '.join(node.edges)}")
            else:
                print("  Connected to: None")
            print("-" * 40)

    def to_dict(self, accepted_only: bool = True) -> dict:
        """
        Convert the graph to a dictionary with accepted_only flag
        """

        graph_dict = {}

        for node in self.nodes.values():
            # 모든 노드 추가
            if not accepted_only:
                graph_dict[node.node_id] = node.instance.model_dump()
                continue

            # Claim이랑 같이 추가
            if isinstance(node.instance, Rationale):
                continue

            # Accepted Claim 여부에 따라 추가
            if isinstance(node.instance, Claim):
                is_accepted = False

                if node.edges:
                    rationale_id = node.edges[0]
                    rationale = self.nodes[rationale_id].instance
                    is_accepted = rationale.is_accepted

                if is_accepted:
                    graph_dict[node.node_id] = node.instance.model_dump()
                    graph_dict[rationale_id] = rationale.model_dump()

                continue

            # 나머지 Thesis, Statement 추가
            graph_dict[node.node_id] = node.instance.model_dump()

        return graph_dict
