import argparse
from typing import List
from typing import Optional
from aether import factory
from aether.clause.graph.base import ClauseGraph
from aether.clause.graph.edge import SUEdgeCalculator
from aether.clause.tree.base import ClauseTree
from aether.clause.tree.generator import ClauseGenerator
from aether.logger import get_logger
from aether.utils import generate_uuid

logger = get_logger(__name__)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-edges", type=int, default=1000)
    parser.add_argument("--sim-thr", type=float, default=0.2)
    parser.add_argument("--weight-thr", type=float, default=0.3)
    parser.add_argument("--min-signal-ratio", type=float, default=0.10)
    parser.add_argument("--max-signal-ratio", type=float, default=0.40)
    parser.add_argument("--max-iterations", type=int, default=1000)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--num-trees", type=int, default=5)
    return parser.parse_args()


def generate_trees(
    generator: ClauseGenerator,
    max_depth: int = 3,
    num_trees: int = 10,
) -> List[ClauseTree]:
    """
    Random Tree Generation
    """
    trees = []

    while len(trees) < num_trees:
        tree = generator.generate(max_depth=max_depth)
        tree.name = str(generate_uuid())

        if tree.iscompleted and tree.depth == max_depth:
            trees.append(tree)

    return trees


def generate_clause(
    trees: List[ClauseTree],
    clause_graph: Optional[ClauseGraph] = None,
    sim_threshold: float = 0.2,
    weight_threshold: float = 0.3,
    min_signal_ratio: float = 0.10,
    max_signal_ratio: float = 0.40,
) -> ClauseGraph:
    """
    Clause Graph Generation
    """
    if not clause_graph:
        clause_graph = ClauseGraph()
        clause_graph.set_edge_calculator(SUEdgeCalculator.calculate)

    clause_graph.add_nodes(
        trees,
        sim_threshold=sim_threshold,
        weight_threshold=weight_threshold,
        min_signal_ratio=min_signal_ratio,
        max_signal_ratio=max_signal_ratio,
    )
    return clause_graph


def main():
    """
    Clause Graph Generation Entrypoint
    """
    args = parse_args()

    provider = factory.get_provider()
    generator = factory.get_clause_generator(provider)

    clause_graph = None
    iter_ = 0

    while True:
        iter_ += 1

        # Tree Random Generation
        trees = generate_trees(
            generator=generator,
            max_depth=args.max_depth,
            num_trees=args.num_trees,
        )
        # Clause Graph Generation
        clause_graph = generate_clause(
            trees=trees,
            clause_graph=clause_graph,
            sim_threshold=args.sim_thr,
            weight_threshold=args.weight_thr,
            min_signal_ratio=args.min_signal_ratio,
            max_signal_ratio=args.max_signal_ratio,
        )

        num_edges = clause_graph.num_edges

        logger.info(f"[Iter: {iter_}] Number of edges: {num_edges}")

        if num_edges > args.num_edges:
            break

    clause_graph.save("clause-graph-v0.json")


if __name__ == "__main__":
    main()
