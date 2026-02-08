import asyncio
import os
from aether.agents.thesis.schema import Thesis
from aether.config import get_config
from aether.config import resolve_path
from aether.logger import get_logger
from aether.pipeline.claim import generate_claims_async
from aether.utils import load_json
from aether.utils import save_json

logger = get_logger(__name__)


def load_all_theses(thesis_load_basedir: str) -> list[Thesis]:
    files = [f for f in os.listdir(thesis_load_basedir) if f.endswith(".json")]
    theses = []
    for f in files:
        filepath = os.path.join(thesis_load_basedir, f)
        thesis_dict = load_json(filepath)
        theses.append(Thesis(**thesis_dict))
    return theses


async def main(
    thesis_load_basedir: str = None,
    claim_save_basedir: str = None,
    num_parallel: int = 4,
):
    config = get_config()
    db_dir = resolve_path(config.data.database_dir)
    thesis_load_basedir = thesis_load_basedir or os.path.join(db_dir, "thesis")
    claim_save_basedir = claim_save_basedir or os.path.join(db_dir, "claim")

    semaphore = asyncio.Semaphore(config.pipeline.max_concurrent_requests)

    theses = load_all_theses(thesis_load_basedir)[:num_parallel]
    logger.info(f"Processing {len(theses)} theses in parallel")

    async def gen_one(thesis):
        async with semaphore:
            return thesis, await generate_claims_async(thesis, config=config)

    results = await asyncio.gather(*[gen_one(t) for t in theses])

    os.makedirs(claim_save_basedir, exist_ok=True)
    all_claims = []

    for thesis, claims in results:
        claims_dict = {c.uuid: c.model_dump() for c in claims}
        savepath = os.path.join(claim_save_basedir, f"claim-{thesis.uuid}.json")
        save_json(claims_dict, savepath)
        logger.info(f"Claims saved: {savepath}")
        all_claims.extend(claims)

    return all_claims


if __name__ == "__main__":
    asyncio.run(main())
