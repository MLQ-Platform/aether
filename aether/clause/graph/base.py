from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
import networkx as nx
from aether.clause.tree.base import ClauseTree
from aether.logger import get_logger
from aether.utils import generate_uuid

logger = get_logger(__name__)


class ClauseGraph:
    """
    ClauseTree들을 노드로 하는 그래프 클래스
    """

    def __init__(self, name: str = "ClauseGraph"):
        self.name = name
        self.graph = nx.Graph()
        self.clause_trees: Dict[int, ClauseTree] = {}
        self.edge_calculator: Optional[Callable] = None

    def __repr__(self):
        return f"ClauseGraph({self.num_nodes} nodes)"

    def add_clause_tree(self, tree: ClauseTree) -> int:
        """
        ClauseTree를 그래프에 노드로 추가
        """
        if type(tree) is not ClauseTree:
            raise ValueError("tree must be a ClauseTree Type")

        node_id = generate_uuid()

        self.graph.add_node(node_id)
        self.clause_trees[node_id] = tree

        logger.info(f"Added ClauseTree as node id: {node_id}")
        return node_id

    def add_clause_trees(self, trees: List[ClauseTree]) -> List[int]:
        """
        여러 ClauseTree를 한번에 추가
        """
        return [self.add_clause_tree(tree) for tree in trees]

    def set_edge_calculator(
        self, calculator: Callable[[ClauseTree, ClauseTree], float]
    ):
        """
        간선 가중치 계산 함수 설정
        """
        self.edge_calculator = calculator
        logger.info("Edge calculator set")

    def compute_all_edges(self, threshold: float = 0.0):
        """
        모든 노드 쌍에 대해 간선 가중치 계산 및 추가
        """

        if self.edge_calculator is None:
            raise ValueError("Edge calculator must be set first")

        node_ids = list(self.clause_trees.keys())
        edges_added = 0

        for i, node_id1 in enumerate(node_ids):
            for node_id2 in node_ids[i + 1 :]:
                # 두 clause tree에 대해 간선 가중치 계산
                tree1 = self.clause_trees[node_id1]
                tree2 = self.clause_trees[node_id2]
                series_a = tree1.evaluate()
                series_b = tree2.evaluate()

                weight = self.edge_calculator(series_a, series_b)

                if weight >= threshold:
                    self.graph.add_edge(node_id1, node_id2, weight=weight)
                    edges_added += 1

        logger.info(f"Added {edges_added} edges with threshold {threshold}")

    def get_neighbors(self, node_id: int) -> List[int]:
        """
        노드의 이웃들 반환
        """
        return list(self.graph.neighbors(node_id))

    def get_edge_weight(self, node_id1: int, node_id2: int) -> Optional[float]:
        """
        두 노드 사이의 간선 가중치 반환
        """
        if self.graph.has_edge(node_id1, node_id2):
            return self.graph.edges[node_id1, node_id2]["weight"]

        return None

    def get_clause_tree(self, node_id: int) -> ClauseTree:
        """
        노드 ID에 해당하는 ClauseTree 반환
        """
        return self.clause_trees[node_id]

    @property
    def num_nodes(self) -> int:
        """
        그래프의 노드 수
        """
        return self.graph.number_of_nodes()

    @property
    def num_edges(self) -> int:
        """
        그래프의 간선 수
        """
        return self.graph.number_of_edges()
