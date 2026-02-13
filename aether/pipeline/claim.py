from aether import factory
from aether.agents.claim.schema import Claim
from aether.agents.thesis.schema import Thesis
from aether.config import Config
from aether.logger import get_logger

logger = get_logger(__name__)


def generate_claims(thesis: Thesis, config: Config = None) -> list[Claim]:
    claim_agent = factory.get_claim_agent(config)
    claims = claim_agent.run(thesis.thesis)
    return [c for c in claims.claims if c is not None and not isinstance(c, Exception)]


async def generate_claims_async(thesis: Thesis, config: Config = None) -> list[Claim]:
    claim_agent = factory.get_claim_agent(config, async_=True)
    claims = await claim_agent.run_async(thesis.thesis)
    return [c for c in claims.claims if c is not None and not isinstance(c, Exception)]
