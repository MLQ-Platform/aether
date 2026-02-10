from aether.agents.claim.schema import Claim
from aether.agents.rationale.schema import Rationale
from aether.agents.statement.graph.node import Node


class StatementGraph:
    """
    Statement Graph
    """

    def __init__(self):
        self.nodes: dict[int, Node] = {}

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
