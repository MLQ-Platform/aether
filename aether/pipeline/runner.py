import asyncio
import os
import time
from aether import factory
from aether.config import Config
from aether.config import get_config
from aether.display import step_progress
from aether.llm.agent import ReactAgent
from aether.logger import get_logger
from aether.pipeline.clause import build_clause_graph
from aether.pipeline.clause import generate_sub_clause
from aether.pipeline.claim import generate_claims
from aether.pipeline.factor import run_factor_revision
from aether.pipeline.statement import generate_statement
from aether.pipeline.statement import generate_statement_graph
from aether.pipeline.statement import verify_claims_loop
from aether.pipeline.thesis import generate_thesis
from aether.utils import save_json

logger = get_logger(__name__)


async def run_full_pipeline(config: Config = None):
    """Run the complete AETHER pipeline: clause -> thesis -> claim -> statement -> factor.

    Returns:
        (factor_code, metrics) tuple where metrics is a dict for display.
    """
    start = time.time()
    config = config or get_config()

    provider = factory.get_provider()
    semaphore = asyncio.Semaphore(config.pipeline.max_concurrent_requests)

    # 1. Clause Graph Generation
    with step_progress("Building Clause Graph") as ctx:
        clause_graph = build_clause_graph(config)
        ctx.detail(f"{clause_graph.num_nodes} nodes, {clause_graph.num_edges} edges")

    # 2. Subgraph Extraction + Thesis Generation
    with step_progress("Generating Thesis") as ctx:
        subclause = generate_sub_clause(clause_graph)
        thesis = generate_thesis(*subclause.clause_trees.values(), config=config)

    # 3. Claim Decomposition
    with step_progress("Decomposing Claims") as ctx:
        claims = generate_claims(thesis, config=config)
        ctx.detail(f"{len(claims)} claims")

    # 4. Rationale Verification Loop
    with step_progress("Verifying Claims") as ctx:
        try:
            final_claims, instances, edges = await verify_claims_loop(
                claims, provider=provider, semaphore=semaphore, config=config
            )
        finally:
            ReactAgent.shutdown()
        accepted = len(final_claims)
        ctx.detail(f"{accepted} claims accepted")

    # Add thesis and original claims to instances/edges for graph
    instances = [thesis] + claims + instances
    edges = [(thesis.uuid, c.uuid) for c in claims] + edges

    # 5. Statement Synthesis
    with step_progress("Synthesizing Statement") as ctx:
        generate_statement_graph(instances, edges)
        statement = generate_statement(final_claims, config=config)

    # 6. Factor Generation
    with step_progress("Generating Factor") as ctx:
        factor_statement, factor_code = run_factor_revision(statement, config=config)
        ctx.detail(f"{len(factor_code.code):,} chars")

    # Save results
    db_dir = config.data.database_dir
    factor_dict = {**factor_statement.model_dump(), **factor_code.model_dump()}
    savepath = os.path.join(db_dir, "factor", f"factor-{factor_statement.uuid}.json")
    os.makedirs(os.path.dirname(savepath), exist_ok=True)
    save_json(factor_dict, savepath)

    elapsed = time.time() - start
    metrics = {
        "duration": f"{elapsed:.1f}s",
        "claims": f"{accepted} accepted",
        "factor_chars": f"{len(factor_code.code):,}",
    }
    return factor_code, metrics
