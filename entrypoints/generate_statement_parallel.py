import asyncio
import os
from typing import List
from aether import factory
from aether.agents.claim.schema import Claim
from aether.config import get_config
from aether.config import resolve_path
from aether.llm.agent import ReactAgent
from aether.logger import get_logger
from aether.pipeline.statement import generate_statement
from aether.pipeline.statement import generate_statement_graph
from aether.pipeline.statement import verify_claims_loop
from aether.utils import load_json
from aether.utils import save_json

logger = get_logger(__name__)


def load_all_claim_sets(claim_load_basedir: str) -> list[list[Claim]]:
    files = [f for f in os.listdir(claim_load_basedir) if f.endswith(".json")]
    claim_sets = []
    for f in files:
        filepath = os.path.join(claim_load_basedir, f)
        claims_dict = load_json(filepath)
        claims = [Claim(**c) for c in claims_dict.values()]
        claim_sets.append(claims)
    return claim_sets


async def process_one(
    claims: List[Claim],
    provider,
    semaphore: asyncio.Semaphore,
    statement_save_basedir: str,
    config=None,
):
    final_claims, instances, edges = await verify_claims_loop(
        claims, provider=provider, semaphore=semaphore, config=config
    )

    instances = list(claims) + instances
    statement = generate_statement(final_claims, config=config)
    logger.info("Statement generated")
    instances.append(statement)

    statement_graph = generate_statement_graph(instances, edges)

    savepath = os.path.join(statement_save_basedir, f"statement-{statement.uuid}.json")
    save_json(statement_graph.to_dict(), savepath)
    logger.info(f"Statement graph saved to {savepath}")

    return statement_graph


async def main(
    claim_load_basedir: str = None,
    statement_save_basedir: str = None,
    num_parallel: int = 4,
):
    config = get_config()
    db_dir = resolve_path(config.data.database_dir)
    claim_load_basedir = claim_load_basedir or os.path.join(db_dir, "claim")
    statement_save_basedir = statement_save_basedir or os.path.join(db_dir, "statement")

    semaphore = asyncio.Semaphore(config.pipeline.max_concurrent_requests)
    provider = factory.get_provider()

    claim_sets = load_all_claim_sets(claim_load_basedir)[:num_parallel]
    logger.info(f"Processing {len(claim_sets)} claim sets in parallel")

    os.makedirs(statement_save_basedir, exist_ok=True)

    try:
        results = await asyncio.gather(
            *[
                process_one(
                    claims, provider, semaphore, statement_save_basedir, config=config
                )
                for claims in claim_sets
            ]
        )
    finally:
        ReactAgent.shutdown()

    return results


if __name__ == "__main__":
    asyncio.run(main())
