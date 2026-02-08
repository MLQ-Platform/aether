import os
from aether.agents.thesis.schema import Thesis
from aether.config import get_config
from aether.config import resolve_path
from aether.logger import get_logger
from aether.pipeline.claim import generate_claims
from aether.utils import load_json
from aether.utils import save_json

logger = get_logger(__name__)


def sample_thesis(thesis_load_basedir: str) -> Thesis:
    files = [f for f in os.listdir(thesis_load_basedir) if f.endswith(".json")]
    filepath = os.path.join(thesis_load_basedir, files[0])
    thesis_dict = load_json(filepath)
    thesis = Thesis(**thesis_dict)
    return thesis


def main(
    thesis_load_basedir: str = None,
    claim_save_basedir: str = None,
):
    config = get_config()
    db_dir = resolve_path(config.data.database_dir)
    thesis_load_basedir = thesis_load_basedir or os.path.join(db_dir, "thesis")
    claim_save_basedir = claim_save_basedir or os.path.join(db_dir, "claim")

    thesis = sample_thesis(thesis_load_basedir)
    claims = generate_claims(thesis, config=config)
    logger.info(f"{len(claims)} claims generated")

    os.makedirs(claim_save_basedir, exist_ok=True)
    claims_dict = {c.uuid: c.model_dump() for c in claims}
    savepath = os.path.join(claim_save_basedir, f"claim-{thesis.uuid}.json")
    save_json(claims_dict, savepath)
    return claims


if __name__ == "__main__":
    main()
