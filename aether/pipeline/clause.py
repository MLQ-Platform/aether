import os
from aether import factory
from aether.clause.graph.base import ClauseGraph
from aether.clause.graph.edge import SUEdgeCalculator
from aether.clause.tree.base import ClauseTree
from aether.clause.tree.generator import ClauseGenerator
from aether.config import Config
from aether.config import get_config
from aether.exceptions import DataError
from aether.logger import get_logger
from aether.utils import generate_id_tag

logger = get_logger(__name__)


def generate_trees(
    generator: ClauseGenerator,
    max_depth: int = None,
    num_trees: int = None,
    config: Config = None,
) -> list[ClauseTree]:
    config = config or get_config()
    max_depth = max_depth if max_depth is not None else config.clause.max_depth
    num_trees = num_trees if num_trees is not None else config.clause.num_trees

    trees = []
    attempts = 0
    max_attempts = num_trees * max(1, config.clause.tree_max_iter)

    while len(trees) < num_trees:
        attempts += 1
        if attempts > max_attempts:
            raise DataError(
                "Failed to generate enough completed trees; "
                f"generated {len(trees)}/{num_trees} after {max_attempts} attempts"
            )
        tree = generator.generate(
            max_depth=max_depth, tree_max_iter=config.clause.tree_max_iter
        )
        tree.name = generate_id_tag()

        if tree.iscompleted and tree.depth == max_depth:
            trees.append(tree)

    return trees


def generate_clause(
    trees: list[ClauseTree],
    clause_graph: ClauseGraph | None = None,
    config: Config = None,
) -> ClauseGraph:
    config = config or get_config()

    if not clause_graph:
        clause_graph = ClauseGraph()
        clause_graph.set_edge_calculator(SUEdgeCalculator.calculate)

    clause_graph.add_nodes(
        trees,
        sim_threshold=config.clause.sim_threshold,
        weight_threshold=config.clause.weight_threshold,
        min_signal_ratio=config.clause.min_signal_ratio,
        max_signal_ratio=config.clause.max_signal_ratio,
    )
    return clause_graph


def generate_sub_clause(
    clause_graph: ClauseGraph, config: Config = None
) -> ClauseGraph:
    from aether.clause.graph.extractor import SubgraphExtractor

    config = config or get_config()
    extractor = SubgraphExtractor(
        clause_graph,
        restart_prob=config.clause.restart_prob,
        length_factor=config.clause.length_factor,
    )
    subgraph = extractor.extract(size=2)
    return subgraph


def load_clause_graph(basedir: str, version: str = "v0") -> ClauseGraph:
    filepath = os.path.join(basedir, f"clause-{version}.json")
    try:
        clause_graph = ClauseGraph.load(filepath)
    except FileNotFoundError as e:
        raise DataError(f"Clause graph not found: {filepath}") from e
    return clause_graph


def build_clause_graph(config: Config = None, on_progress=None) -> ClauseGraph:
    """
    Build a clause graph from scratch using config parameters.

    Args:
        config: Config object.
        on_progress: Optional callback(num_edges, iteration) for live UI updates.
    """
    config = config or get_config()
    provider = factory.get_provider()
    generator = factory.get_clause_generator(provider, config)

    clause_graph = None

    for iter_ in range(config.clause.max_iterations):
        trees = generate_trees(generator, config=config)
        clause_graph = generate_clause(trees, clause_graph=clause_graph, config=config)

        num_edges = clause_graph.num_edges
        logger.info(f"Clause iteration {iter_ + 1}: {num_edges} edges")

        if on_progress:
            on_progress(num_edges, iter_ + 1)

        if num_edges > config.clause.num_edges:
            break

    return clause_graph
