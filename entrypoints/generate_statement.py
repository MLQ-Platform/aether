import asyncio
import os
from typing import List
from aether import factory
from aether.agents.claim.schema import Claim
from aether.config import get_config
from aether.llm.agent import ReactAgent
from aether.logger import get_logger
from aether.pipeline.statement import generate_statement
from aether.pipeline.statement import generate_statement_graph
from aether.pipeline.statement import verify_claims_loop
from aether.utils import load_json
from aether.utils import save_json

logger = get_logger(__name__)


def sample_claims(claim_load_basedir: str) -> List[Claim]:
    files = [f for f in os.listdir(claim_load_basedir) if f.endswith(".json")]
    filepath = os.path.join(claim_load_basedir, files[0])
    claims_dict = load_json(filepath)
    claims = [Claim(**c) for c in claims_dict.values()]
    return claims


async def main(
    claim_load_basedir: str = None,
    statement_save_basedir: str = None,
):
    config = get_config()
    db_dir = config.data.database_dir
    claim_load_basedir = claim_load_basedir or os.path.join(db_dir, "claim")
    statement_save_basedir = statement_save_basedir or os.path.join(db_dir, "statement")

    semaphore = asyncio.Semaphore(config.pipeline.max_concurrent_requests)
    provider = factory.get_provider()

    claims = sample_claims(claim_load_basedir)
    logger.info(f"{len(claims)} claims loaded")

    try:
        final_claims, instances, edges = await verify_claims_loop(
            claims, provider=provider, semaphore=semaphore, config=config
        )

        # Add original claims to instances for graph
        instances = list(claims) + instances

        statement = generate_statement(final_claims, config=config)
        logger.info("Statement generated")
        instances.append(statement)

        statement_graph = generate_statement_graph(instances, edges)

        os.makedirs(statement_save_basedir, exist_ok=True)
        savepath = os.path.join(
            statement_save_basedir, f"statement-{statement.uuid}.json"
        )
        save_json(statement_graph.to_dict(), savepath)
        logger.info(f"Statement graph saved to {savepath}")

    except Exception as e:
        logger.error(f"Statement generation failed: {e}")
        raise e

    finally:
        ReactAgent.shutdown()

    return statement_graph


if __name__ == "__main__":
    asyncio.run(main())
