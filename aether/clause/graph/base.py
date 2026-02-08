import json
from pathlib import Path
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
import networkx as nx
import pandas as pd
from aether.clause.tree.base import ClauseTree
from aether.logger import get_logger

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

    def set_edge_calculator(
        self, calculator: Callable[[ClauseTree, ClauseTree], float]
    ):
        """
        간선 가중치 계산 함수 설정
        """
        self.edge_calculator = calculator
        logger.debug("Edge calculator set")

    def add_nodes(
        self,
        trees: List[ClauseTree],
        sim_threshold: float = 0.2,
        weight_threshold: float = 0.0,
        min_signal_ratio: float = 0.10,
        max_signal_ratio: float = 0.40,
    ):
        """
        모든 노드 쌍에 대해 간선 가중치 계산 및 추가
        """

        if self.edge_calculator is None:
            raise ValueError("Edge calculator must be set first")

        edges_added = 0
        for i, tree1 in enumerate(trees):
            for tree2 in trees[i + 1 :]:
                series_a = tree1.evaluate()
                series_b = tree2.evaluate()

                # Filter 1
                if not self._filter_with_ratio(
                    series_a,
                    series_b,
                    min_signal_ratio,
                    max_signal_ratio,
                ):
                    continue

                # Filter 2
                if not self._filter_with_similarity(
                    tree1,
                    tree2,
                    sim_threshold,
                ):
                    continue

                weight = self.edge_calculator(series_a, series_b)

                if weight >= weight_threshold:
                    self.graph.add_node(tree1.tree_id)
                    self.graph.add_node(tree2.tree_id)
                    self.graph.add_edge(tree1.tree_id, tree2.tree_id, weight=weight)
                    self.clause_trees[tree1.tree_id] = tree1
                    self.clause_trees[tree2.tree_id] = tree2
                    edges_added += 1

        logger.info(f"{edges_added} edges added")

    def _filter_with_ratio(
        self,
        series_a: pd.Series,
        series_b: pd.Series,
        min_ratio: float,
        max_ratio: float,
    ) -> bool:
        """
        Signal Ratio based Filtering
        """
        ratio_a = series_a.sum() / len(series_a)
        ratio_b = series_b.sum() / len(series_b)

        if ratio_a < min_ratio or ratio_a > max_ratio:
            return False

        if ratio_b < min_ratio or ratio_b > max_ratio:
            return False

        return True

    def _filter_with_similarity(
        self,
        tree_a: ClauseTree,
        tree_b: ClauseTree,
        threshold: float,
    ) -> bool:
        """
        Jaccard Similarity based Filtering
        """
        nodes_a = [str(n) for n in tree_a.nodes]
        nodes_b = [str(n) for n in tree_b.nodes]

        similarity = len(set(nodes_a) & set(nodes_b)) / len(set(nodes_a) | set(nodes_b))
        return similarity <= threshold

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

    def get_edges(self, data=True) -> List[Tuple[int, int, dict]]:
        """
        모든 간선 반환
        """
        return list(self.graph.edges(data=data))

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

    def to_dict(self) -> dict:
        """
        ClauseGraph를 딕셔너리로 변환
        """

        return {
            "name": self.name,
            "graph": nx.node_link_data(self.graph, edges="links"),
            "clause_trees": {
                tree_id: tree.to_dict() for tree_id, tree in self.clause_trees.items()
            },
        }

    def save(self, filepath: str):
        """
        ClauseGraph를 JSON 파일로 저장
        """

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"ClauseGraph saved to {filepath}")

    @classmethod
    def from_dict(cls, data: dict) -> "ClauseGraph":
        """
        딕셔너리에서 ClauseGraph 인스턴스 생성
        """

        graph = cls(name=data["name"])
        graph.graph = nx.node_link_graph(data["graph"], edges="links")
        graph.clause_trees = {
            int(tree_id): ClauseTree.from_dict(tree_data)
            for tree_id, tree_data in data["clause_trees"].items()
        }

        logger.debug(f"ClauseGraph loaded ({graph.num_nodes} nodes)")
        return graph

    @classmethod
    def load(cls, filepath: str) -> "ClauseGraph":
        """
        JSON 파일에서 ClauseGraph 인스턴스 생성
        """

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        logger.info(f"ClauseGraph loaded from {filepath}")
        return cls.from_dict(data)
