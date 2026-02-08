import pytest
from unittest.mock import MagicMock
from unittest.mock import patch
from pydantic import BaseModel
from aether.pipeline.statement import generate_statement_graph
from aether.pipeline.statement import get_final_claims
from aether.agents.claim.schema import Claim
from aether.agents.rationale.schema import Rationale


class DummyInstance(BaseModel):
    uuid: int = 1
    value: str = "test"


class TestGenerateStatementGraph:
    def test_creates_graph_with_nodes(self):
        instances = [
            DummyInstance(uuid=1, value="a"),
            DummyInstance(uuid=2, value="b"),
        ]
        edges = [(1, 2)]

        graph = generate_statement_graph(instances, edges)

        assert len(graph.nodes) == 2
        assert 1 in graph.nodes
        assert 2 in graph.nodes

    def test_empty_graph(self):
        graph = generate_statement_graph([], [])
        assert len(graph.nodes) == 0

    def test_graph_with_no_edges(self):
        instances = [DummyInstance(uuid=1)]
        graph = generate_statement_graph(instances, [])
        assert len(graph.nodes) == 1
