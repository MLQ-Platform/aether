from typing import List
from aether import factory
from aether.agents.claim.schema import Claim
from aether.agents.thesis.schema import Thesis
from aether.config import Config
from aether.logger import get_logger
from aether.utils import add_uuid

logger = get_logger(__name__)


def generate_claims(thesis: Thesis, config: Config = None) -> List[Claim]:
    claim_agent = factory.get_claim_agent(config)
    claims = claim_agent.run(thesis.thesis)
    claims = add_uuid(claims.claims)
    return claims


async def generate_claims_async(thesis: Thesis, config: Config = None) -> List[Claim]:
    claim_agent = factory.get_async_claim_agent(config)
    claims = await claim_agent.run_async(thesis.thesis)
    claims = add_uuid(claims.claims)
    return claims
