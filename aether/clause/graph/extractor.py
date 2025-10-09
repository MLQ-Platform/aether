import random
from typing import Set
import networkx as nx
import numpy as np
from aether.clause.graph.base import ClauseGraph
from aether.logger import get_logger
from aether.utils import generate_uuid

logger = get_logger(__name__)


class SubgraphExtractor:
    """
    Random walk based subgraph extraction from ClauseGraph
    """

    RESTART_PROB = 0.1
    LENGTH_FACTOR = 2.0

    def __init__(self, graph: ClauseGraph):
        self.graph = graph

    @classmethod
    def set_params(cls, restart_prob: float, length_factor: float):
        cls.RESTART_PROB = restart_prob
        cls.LENGTH_FACTOR = length_factor

    def extract(self, size: int, start_node: str) -> ClauseGraph:
        """
        Extract subgraph using random walk
        """

        if (
            size <= 0
            or size > self.graph.num_nodes
            or start_node not in self.graph.clause_trees
        ):
            raise ValueError("Invalid size or start node")

        visited = self._traverse(size, start_node)
        subgraph = self._build(visited)
        return subgraph

    def _traverse(self, size: int, start: str) -> Set[str]:
        """
        Perform random walk to collect nodes
        """

        visited = {start}
        current = start

        for _ in range(int(size * self.LENGTH_FACTOR)):
            if len(visited) >= size:
                break

            # Restart probability
            if random.random() < self.RESTART_PROB:
                current = start
                continue

            # Get unvisited neighbors
            neighbors = [
                n for n in self.graph.get_neighbors(current) if n not in visited
            ]

            if not neighbors:
                current = start
                continue

            # Select next node by weight
            weights = [self.graph.get_edge_weight(current, n) for n in neighbors]
            total = sum(weights)

            if total > 0:
                probs = [w / total for w in weights]
                current = np.random.choice(neighbors, p=probs)
            else:
                current = random.choice(neighbors)

            visited.add(str(current))

        logger.info(f"Random walk completed. Final size: {len(visited)}")
        return visited

    def _build(self, nodes: Set[str]) -> nx.Graph:
        """
        Build NetworkX subgraph from nodes
        """
        trees = [self.graph.clause_trees[node] for node in nodes]

        tree_id = generate_uuid()
        subgraph = ClauseGraph(tree_id)
        subgraph.add_clause_trees(trees, nodes)

        node_list = list(subgraph.clause_trees.keys())

        for i, n1 in enumerate(node_list):
            for n2 in node_list[i + 1 :]:
                weight = self.graph.get_edge_weight(n1, n2)

                if weight is not None:
                    subgraph.add_edge(n1, n2, weight=weight)

        return subgraph
