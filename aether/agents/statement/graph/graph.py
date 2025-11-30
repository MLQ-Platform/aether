from typing import Dict
from typing import List
from aether.agents.statement.graph.node import Node


class StatementGraph:
    """
    Statement Graph
    """

    def __init__(self):
        self.nodes: Dict[str, Node] = {}

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
            print(f"Node ID: {nid}")
            print(f"  Type: {node.node_type}")
            if node.edges:
                print(f"  Connected to: {', '.join(node.edges)}")
            else:
                print("  Connected to: None")
            print("-" * 40)
