import asyncio
from aether import factory
from aether.agents.claim.schema import Claim
from aether.agents.rationale.agent import RationaleAgent
from aether.agents.rationale.schema import Rationale
from aether.agents.statement.schema import Statement
from aether.config import Config
from aether.config import get_config
from aether.logger import get_logger
from aether.provider import InMemoryDataProvider

logger = get_logger(__name__)


async def verify_claims_loop(
    claims: list[Claim],
    provider: InMemoryDataProvider,
    semaphore: asyncio.Semaphore,
    config: Config = None,
) -> tuple[list[Claim], list[dict]]:
    """Run the iterative claim verification loop.

    Returns:
        (final_claims, sequence) where:
        - final_claims: Claims that were accepted across all iterations
        - sequence: Ordered timeline for persistence
          claims -> rationales -> claims -> ... -> final claims
    """
    config = config or get_config()
    sequence: list[dict] = [
        {"type": "claims", "items": [c.model_dump() for c in claims]}
    ]

    final_claims = []
    # Reuse agents across rounds to avoid recreating clients
    rationale_agent = factory.get_rationale_agent(config)
    modify_agent = factory.get_claim_modify_agent(config)

    for i in range(config.pipeline.total_iterations):
        logger.info(
            f"Verification round {i + 1}/{config.pipeline.total_iterations} ({len(claims)} claims)"
        )

        rationales = await generate_rationales_async(
            claims,
            provider=provider,
            semaphore=semaphore,
            rationale_agent=rationale_agent,
            config=config,
        )

        pairs = list(zip(claims, rationales))
        rejected_rationales = [r for c, r in pairs if not r.is_accepted]
        rejected_claims = [c for c, r in pairs if not r.is_accepted]
        accepted_claims = [c for c, r in pairs if r.is_accepted]
        final_claims.extend(accepted_claims)

        logger.info(
            f"Accepted {len(accepted_claims)}/{len(claims)}, rejected {len(rejected_rationales)}"
        )

        sequence.append(
            {
                "type": "rationales",
                "items": [r.model_dump() for r in rationales],
            }
        )

        if not rejected_rationales:
            logger.info("All claims accepted")
            break

        if rejected_claims:
            logger.info(f"Modifying {len(rejected_claims)} rejected claims")
            modified_claims = await generate_rationales_modify_async(
                rejected_claims,
                rejected_rationales,
                semaphore=semaphore,
                modify_agent=modify_agent,
                config=config,
            )

            claims = modified_claims

        sequence.append({"type": "claims", "items": [c.model_dump() for c in claims]})

    return final_claims, sequence


async def generate_rationales_async(
    claims: list[Claim],
    provider: InMemoryDataProvider,
    semaphore: asyncio.Semaphore,
    rationale_agent: RationaleAgent | None = None,
    config: Config = None,
) -> list[Rationale]:
    config = config or get_config()
    if rationale_agent is None:
        rationale_agent = factory.get_rationale_agent(config)
    exec_context = {"df": provider.get(config.data.ticker)}
    completed = 0

    async def limited(claim):
        nonlocal completed
        async with semaphore:
            result = await rationale_agent.run_async(
                claim, exec_context=exec_context.copy()
            )
            completed += 1
            logger.info(f"Claim verified {completed}/{len(claims)}")
            return result

    tasks = [limited(claim) for claim in claims]
    return await asyncio.gather(*tasks)


async def generate_rationales_modify_async(
    claims: list[Claim],
    rationales: list[Rationale],
    semaphore: asyncio.Semaphore,
    modify_agent=None,
    config: Config = None,
) -> list[Claim]:
    config = config or get_config()
    if modify_agent is None:
        modify_agent = factory.get_claim_modify_agent(config)

    async def limited(claim, rationale):
        async with semaphore:
            return await modify_agent.run_async(claim, rationale.rationale)

    tasks = [limited(claim, rationale) for claim, rationale in zip(claims, rationales)]
    return await asyncio.gather(*tasks)


def generate_statement(
    final_claims: list[Claim],
    config: Config = None,
) -> Statement:
    statement_agent = factory.get_statement_agent(config)
    return statement_agent.run(final_claims)
