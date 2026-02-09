import asyncio
from typing import List
from typing import Tuple
from pydantic import BaseModel
from aether import factory
from aether.agents.claim.schema import Claim
from aether.agents.claim.schema import ClaimList
from aether.agents.rationale.schema import Rationale
from aether.agents.statement.graph import StatementGraph
from aether.agents.statement.graph.node import Node
from aether.agents.statement.schema import Statement
from aether.config import Config
from aether.config import get_config
from aether.logger import get_logger
from aether.provider import InMemoryDataProvider
from aether.utils import add_uuid
from aether.utils import generate_uuid

logger = get_logger(__name__)


async def verify_claims_loop(
    claims: List[Claim],
    provider: InMemoryDataProvider,
    semaphore: asyncio.Semaphore,
    config: Config = None,
) -> Tuple[List[Claim], List[BaseModel], List[Tuple[str, str]]]:
    """Run the iterative claim verification loop.

    Returns:
        (final_claims, instances, edges) where:
        - final_claims: Claims that were accepted across all iterations
        - instances: All intermediate rationales and modified claims
        - edges: All intermediate edges for graph building
    """
    config = config or get_config()
    instances = []
    edges = []
    final_claims = []

    for i in range(config.pipeline.total_iterations):
        logger.info(f"Verification round {i + 1}/{config.pipeline.total_iterations}")

        rationales = await generate_rationales_async(
            claims, provider=provider, semaphore=semaphore, config=config
        )

        rejected_rationales: List[Rationale] = [
            x[1] for x in zip(claims, rationales) if not x[1].is_accepted
        ]
        rejected_claims: List[Claim] = [
            x[0] for x in zip(claims, rationales) if not x[1].is_accepted
        ]
        accepted_claims: List[Claim] = [
            x[0] for x in zip(claims, rationales) if x[1].is_accepted
        ]
        final_claims.extend(accepted_claims)

        logger.info(
            f"Rejected: {len(rejected_rationales)}, Accepted: {len(accepted_claims)}"
        )

        instances.extend(rationales)
        edges.extend([(c.uuid, r.uuid) for c, r in zip(claims, rationales)])

        if not rejected_rationales:
            logger.info("All claims accepted")
            break

        modified_claims = await generate_rationales_modify_async(
            rejected_claims, rejected_rationales, semaphore=semaphore, config=config
        )

        instances.extend(modified_claims)
        edges.extend(
            [(r.uuid, c.uuid) for r, c in zip(rejected_rationales, modified_claims)]
        )

        claims = modified_claims

    return final_claims, instances, edges


async def generate_rationales_async(
    claims: List[Claim],
    provider: InMemoryDataProvider,
    semaphore: asyncio.Semaphore,
    config: Config = None,
) -> List[Rationale]:
    config = config or get_config()
    rationale_agent = factory.get_rationale_agent(config)
    exec_context = {"df": provider.get(config.data.ticker)}

    async def limited(claim):
        async with semaphore:
            return await rationale_agent.run_async(
                claim, exec_context=exec_context.copy()
            )

    tasks = [limited(claim) for claim in claims]
    rationales = await asyncio.gather(*tasks, return_exceptions=True)
    rationales = add_uuid(rationales)
    return rationales


async def generate_rationales_modify_async(
    claims: List[Claim],
    rationales: List[Rationale],
    semaphore: asyncio.Semaphore,
    config: Config = None,
) -> List[Claim]:
    config = config or get_config()
    modify_agent = factory.get_claim_modify_agent(config)

    async def limited(claim, rationale):
        async with semaphore:
            return await modify_agent.run_async(claim, rationale.rationale)

    tasks = [limited(claim, rationale) for claim, rationale in zip(claims, rationales)]
    claims: ClaimList = await asyncio.gather(*tasks, return_exceptions=True)
    claims: List[Claim] = add_uuid(claims)
    return claims


def generate_statement(
    final_claims: List[Claim],
    config: Config = None,
) -> Statement:
    statement_agent = factory.get_statement_agent(config)
    statement = statement_agent.run(final_claims)
    statement.uuid = generate_uuid()
    return statement


async def generate_statement_async(
    final_claims: List[Claim],
    config: Config = None,
) -> Statement:
    statement_agent = factory.get_statement_agent(config, async_=True)
    statement = await statement_agent.run_async(final_claims)
    statement.uuid = generate_uuid()
    return statement


def generate_statement_graph(
    instances: List[BaseModel],
    edges: List[Tuple[str, str]],
) -> StatementGraph:
    graph = StatementGraph()

    for instance in instances:
        node = Node(
            instance=instance,
            node_type=type(instance),
            node_id=instance.uuid,
        )
        graph.add_node(node)

    for edge in edges:
        graph.add_edge(*edge)

    return graph


def get_final_claims(statement_graph: StatementGraph) -> List[Claim]:
    final_claims = []

    for node in statement_graph.nodes.values():
        if type(node.instance) is Claim:
            if node.edges:
                rationale_id = node.edges[0]
                rationale = statement_graph.nodes[rationale_id].instance

                if rationale.is_accepted:
                    final_claims.append(node.instance)

            else:
                final_claims.append(node.instance)

    return final_claims
