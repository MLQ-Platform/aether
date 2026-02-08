import asyncio
import os
from aether.config import get_config
from aether.config import resolve_path
from aether.logger import get_logger
from aether.pipeline.clause import generate_sub_clause
from aether.pipeline.clause import load_clause_graph
from aether.pipeline.thesis import generate_thesis_async
from aether.utils import save_json

logger = get_logger(__name__)


async def main(
    clause_load_basedir: str = None,
    thesis_save_basedir: str = None,
    clause_version: str = "v0",
    num_parallel: int = 4,
):
    config = get_config()
    db_dir = resolve_path(config.data.database_dir)
    clause_load_basedir = clause_load_basedir or os.path.join(db_dir, "clause")
    thesis_save_basedir = thesis_save_basedir or os.path.join(db_dir, "thesis")

    clause_graph = load_clause_graph(clause_load_basedir, version=clause_version)
    semaphore = asyncio.Semaphore(config.pipeline.max_concurrent_requests)

    subgraphs = [generate_sub_clause(clause_graph) for _ in range(num_parallel)]

    async def gen_one(subgraph):
        async with semaphore:
            return await generate_thesis_async(
                *subgraph.clause_trees.values(), config=config
            )

    theses = await asyncio.gather(*[gen_one(sg) for sg in subgraphs])
    os.makedirs(thesis_save_basedir, exist_ok=True)

    for thesis in theses:
        savepath = os.path.join(thesis_save_basedir, f"thesis-{thesis.uuid}.json")
        save_json(thesis.model_dump(), savepath)
        logger.info(f"Thesis saved: {savepath}")

    return theses


if __name__ == "__main__":
    asyncio.run(main())
