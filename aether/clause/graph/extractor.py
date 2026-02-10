import random
import numpy as np
from aether.clause.graph.base import ClauseGraph
from aether.logger import get_logger

logger = get_logger(__name__)


class SubgraphExtractor:
    """
    Random walk based subgraph extraction from ClauseGraph
    """

    RESTART_PROB = 0.1
    LENGTH_FACTOR = 2.0

    def __init__(self, graph: ClauseGraph):
        self.graph = graph

    def extract(self, size: int, start_node: int | None = None) -> ClauseGraph:
        """
        Extract subgraph using random walk
        """
        if start_node is None:
            start_node = random.choice(list(self.graph.clause_trees.keys()))

        if (
            size <= 0
            or size > self.graph.num_nodes
            or start_node not in self.graph.clause_trees
        ):
            raise ValueError("Invalid size or start node")

        visited = self._traverse(size, start_node)
        subgraph = self._build(visited)

        nodes = subgraph.num_nodes
        edges = subgraph.num_edges

        logger.debug(f"Subgraph extracted ({nodes} nodes, {edges} edges)")
        return subgraph

    def _traverse(self, size: int, start: int) -> set[int]:
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
                current = int(np.random.choice(neighbors, p=probs))
            else:
                current = random.choice(neighbors)

            visited.add(current)

        return visited

    def _build(self, node_ids: set[int]) -> ClauseGraph:
        """
        Build ClauseGraph subgraph from nodes
        """
        subgraph = ClauseGraph()
        node_list = list(node_ids)  # Set을 list로 변환

        for i, node_id1 in enumerate(node_list):
            for node_id2 in node_list[i + 1 :]:
                weight = self.graph.get_edge_weight(node_id1, node_id2)

                if weight is not None:
                    subgraph.graph.add_node(node_id1)
                    subgraph.graph.add_node(node_id2)
                    subgraph.graph.add_edge(node_id1, node_id2, weight=weight)
                    subgraph.clause_trees[node_id1] = self.graph.clause_trees[node_id1]
                    subgraph.clause_trees[node_id2] = self.graph.clause_trees[node_id2]

        return subgraph
