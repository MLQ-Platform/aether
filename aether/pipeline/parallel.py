import asyncio
import os
from typing import List
import ray
from aether.config import Config
from aether.config import get_config
from aether.logger import get_logger

logger = get_logger(__name__)


def _run_single_pipeline(subgraph_json: dict, config_yaml_path: str) -> dict:
    """
    Run a single hypothesis pipeline in a Ray worker.

    This function is designed to be called inside a Ray remote function.
    Each worker independently loads config, data, and runs the full pipeline.
    """
    from aether import factory
    from aether.clause.graph import ClauseGraph
    from aether.config import Config
    from aether.pipeline.claim import generate_claims
    from aether.pipeline.factor import run_factor_revision
    from aether.pipeline.statement import generate_statement
    from aether.pipeline.statement import verify_claims_loop
    from aether.pipeline.thesis import generate_thesis

    config = Config.from_yaml(config_yaml_path)
    semaphore = asyncio.Semaphore(config.pipeline.max_concurrent_requests)
    provider = factory.get_provider()

    # Reconstruct subgraph from JSON
    subgraph = ClauseGraph.load_from_dict(subgraph_json)
    trees = list(subgraph.clause_trees.values())

    if len(trees) < 2:
        return {"error": "Subgraph has fewer than 2 trees"}

    # Thesis
    thesis = generate_thesis(trees[0], trees[1], config=config)

    # Claims
    claims = generate_claims(thesis, config=config)
    if not claims:
        return {"error": "No claims generated"}

    # Rationale verification loop
    final_claims, _, _ = asyncio.run(
        verify_claims_loop(
            claims, provider=provider, semaphore=semaphore, config=config
        )
    )

    # Statement
    statement = generate_statement(final_claims, config=config)

    # Factor
    factor_statement, factor_code = run_factor_revision(statement, config=config)

    return {
        "thesis": thesis.model_dump(),
        "statement": statement.model_dump(),
        "factor_statement": factor_statement.model_dump(),
        "factor_code": factor_code.model_dump(),
    }


def run_parallel(
    num_pipelines: int = 4,
    config: Config = None,
    config_path: str = "config/aether.yaml",
) -> List[dict]:
    """
    Run multiple hypothesis pipelines in parallel using Ray.

    Args:
        num_pipelines: Number of independent pipelines to run.
        config: Config object (used for clause graph generation).
        config_path: Path to config YAML (passed to Ray workers).

    Returns:
        List of result dicts from each pipeline.
    """

    config = config or get_config(config_path)

    # Define Ray remote function
    @ray.remote
    def _remote_pipeline(subgraph_json: dict, cfg_path: str) -> dict:
        return _run_single_pipeline(subgraph_json, cfg_path)

    # Initialize Ray
    ray.init(ignore_reinit_error=True)

    try:
        # 1. Build clause graph in main process
        logger.info("Building clause graph")
        from aether.pipeline.clause import build_clause_graph
        from aether.pipeline.clause import generate_sub_clause

        clause_graph = build_clause_graph(config)
        logger.info(
            f"Clause graph built ({clause_graph.num_nodes} nodes, "
            f"{clause_graph.num_edges} edges)"
        )

        # 2. Extract multiple subgraphs
        logger.info(f"Extracting {num_pipelines} subgraphs")
        subgraphs = []
        for _ in range(num_pipelines):
            sg = generate_sub_clause(clause_graph)
            subgraphs.append(sg.to_dict())

        # 3. Launch parallel pipelines
        logger.info(f"Launching {num_pipelines} pipeline workers")
        futures = [
            _remote_pipeline.remote(sg_json, config_path) for sg_json in subgraphs
        ]

        # 4. Collect results
        results = ray.get(futures)
        logger.info(f"{len(results)} pipelines completed")

        # 5. Save results
        db_dir = config.data.database_dir
        factor_dir = os.path.join(db_dir, "factor")
        os.makedirs(factor_dir, exist_ok=True)

        from aether.utils import save_json

        for i, result in enumerate(results):
            if "error" not in result:
                uuid = result.get("factor_statement", {}).get("uuid", i)
                savepath = os.path.join(factor_dir, f"factor-{uuid}.json")
                save_json(result, savepath)
                logger.info(f"Pipeline {i + 1} saved to {savepath}")
            else:
                logger.warning(f"Pipeline {i + 1} failed: {result['error']}")

        return results

    finally:
        ray.shutdown()
