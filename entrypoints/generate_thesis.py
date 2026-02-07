import os
from aether import factory
from aether.agents.thesis.schema import Thesis
from aether.clause.graph import ClauseGraph
from aether.clause.tree.base import ClauseTree
from aether.logger import get_logger
from aether.utils import generate_uuid
from aether.utils import save_json

logger = get_logger(__name__)


def load_clause_graph(basedir: str) -> ClauseGraph:
    filepath = os.path.join(basedir, "clause-v0.json")
    clause_graph = ClauseGraph.load(filepath)
    return clause_graph


def generate_sub_clause(clause_graph: ClauseGraph) -> ClauseGraph:
    from aether.clause.graph.extractor import SubgraphExtractor

    extractor = SubgraphExtractor(clause_graph)
    subgraph = extractor.extract(size=2)
    return subgraph


def generate_thesis(tree_a: ClauseTree, tree_b: ClauseTree) -> Thesis:
    thesis_agent = factory.get_thesis_agent()
    thesis = thesis_agent.run(tree_a, tree_b)
    thesis.uuid = generate_uuid()
    return thesis


def main(
    clause_load_basedir: str,
    thesis_save_basedir: str,
):

    # Clause Graph 로드
    clause_graph = load_clause_graph(clause_load_basedir)
    # Clause Graph에서 Sub-Clause 추출
    subclause = generate_sub_clause(clause_graph)
    # Thesis 생성
    logger.info("[Done] Subclause Extracted")
    logger.info("[Start] Thesis Generation")
    thesis = generate_thesis(*subclause.clause_trees.values())
    # Thesis로 Claim 생성
    logger.info(f"[Done] Thesis Generated: {thesis.thesis}")

    savepath = os.path.join(thesis_save_basedir, f"thesis-{thesis.uuid}.json")
    save_json(thesis.model_dump(), savepath)
    return thesis


if __name__ == "__main__":
    thesis = main(
        clause_load_basedir="database/clause",
        thesis_save_basedir="database/thesis",
    )
