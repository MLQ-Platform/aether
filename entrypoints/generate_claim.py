import os
from typing import List
from aether import factory
from aether.agents.claim.schema import Claim
from aether.agents.thesis.schema import Thesis
from aether.logger import get_logger
from aether.utils import add_uuid
from aether.utils import load_json
from aether.utils import save_json

logger = get_logger(__name__)


def sample_thesis(thesis_load_basedir: str) -> Thesis:
    # thesis_load_basedir 디렉토리에서 아무 json 파일이나 하나 선택하도록 변경
    files = [f for f in os.listdir(thesis_load_basedir) if f.endswith(".json")]
    filepath = os.path.join(thesis_load_basedir, files[0])
    thesis_dict = load_json(filepath)
    thesis = Thesis(**thesis_dict)
    return thesis


def generate_claims(thesis: Thesis) -> List[Claim]:
    claim_agent = factory.get_claim_agent()
    claims = claim_agent.run(thesis.thesis)
    claims = add_uuid(claims.claims)
    return claims


def main(
    thesis_load_basedir: str,
    claim_save_basedir: str,
):
    # Thesis 로드
    thesis = sample_thesis(thesis_load_basedir)
    logger.info(f"[Done] Thesis Loaded: {thesis.thesis}")
    # Thesis로 Claim 생성
    claims = generate_claims(thesis)
    logger.info(f"[Done] Claims Generated: {len(claims)}")

    claims_dict = {c.uuid: c.model_dump() for c in claims}
    savepath = os.path.join(claim_save_basedir, f"claim-{thesis.uuid}.json")
    save_json(claims_dict, savepath)
    logger.info("[Done] Claims Saved")
    return claims


if __name__ == "__main__":
    claims = main(
        thesis_load_basedir="database/thesis",
        claim_save_basedir="database/claim",
    )
