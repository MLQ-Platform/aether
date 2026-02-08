import asyncio
import os
from aether.agents.statement.schema import Statement
from aether.config import get_config
from aether.config import resolve_path
from aether.logger import get_logger
from aether.pipeline.factor import run_factor_revision_async
from aether.utils import load_json
from aether.utils import save_json

logger = get_logger(__name__)


def load_all_statements(statement_load_basedir: str) -> list[Statement]:
    files = [f for f in os.listdir(statement_load_basedir) if f.endswith(".json")]
    statements = []
    for f in files:
        filepath = os.path.join(statement_load_basedir, f)
        statement_graph = load_json(filepath)
        statement_str = list(statement_graph.values())[-1]["statement"]
        statement_uuid = list(statement_graph.values())[-1]["uuid"]
        statements.append(Statement(uuid=statement_uuid, statement=statement_str))
    return statements


async def main(
    statement_load_basedir: str = None,
    factor_save_basedir: str = None,
    num_parallel: int = 4,
):
    config = get_config()
    db_dir = resolve_path(config.data.database_dir)
    statement_load_basedir = statement_load_basedir or os.path.join(db_dir, "statement")
    factor_save_basedir = factor_save_basedir or os.path.join(db_dir, "factor")

    semaphore = asyncio.Semaphore(config.pipeline.max_concurrent_requests)

    statements = load_all_statements(statement_load_basedir)[:num_parallel]
    logger.info(f"Processing {len(statements)} statements in parallel")

    async def gen_one(statement):
        async with semaphore:
            return await run_factor_revision_async(statement, config=config)

    results = await asyncio.gather(*[gen_one(s) for s in statements])

    os.makedirs(factor_save_basedir, exist_ok=True)

    for factor_statement, factor_code in results:
        factor_dict = {**factor_statement.model_dump(), **factor_code.model_dump()}
        savepath = os.path.join(
            factor_save_basedir, f"factor-{factor_statement.uuid}.json"
        )
        save_json(factor_dict, savepath)
        logger.info(f"Factor saved to {savepath}")

    return results


if __name__ == "__main__":
    asyncio.run(main())
