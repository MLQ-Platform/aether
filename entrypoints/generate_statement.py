import asyncio
import os
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
from aether.llm.agent import ReactAgent
from aether.logger import get_logger
from aether.provider import InMemoryDataProvider
from aether.utils import add_uuid
from aether.utils import generate_uuid
from aether.utils import load_json
from aether.utils import save_json

logger = get_logger(__name__)


def sample_claims(claim_load_basedir: str) -> List[Claim]:
    files = [f for f in os.listdir(claim_load_basedir) if f.endswith(".json")]
    filepath = os.path.join(claim_load_basedir, files[0])
    claims_dict = load_json(filepath)
    claims = [Claim(**c) for c in claims_dict.values()]
    return claims


def generate_statement(final_claims: List[Claim]) -> Statement:
    statement_agent = factory.get_statement_agent()
    statement = statement_agent.run(final_claims)
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


async def generate_rationales_async(
    claims: List[Claim], provider: InMemoryDataProvider
) -> List[Rationale]:
    """
    Get Rationales Async
    """
    rationale_agent = factory.get_rationale_agent()

    exec_context = {"df": provider.get("BTCUSDT")}

    # Process all claims concurrently
    # Each claim gets a copy of exec_context to avoid shared state issues
    tasks = [
        rationale_agent.run_async(claim, exec_context=exec_context.copy())
        for claim in claims
    ]
    rationales = await asyncio.gather(*tasks, return_exceptions=True)
    rationales = add_uuid(rationales)
    return rationales


async def generate_rationales_modify_async(
    claims: List[Claim], rationales: List[Rationale]
) -> List[Claim]:
    """
    Get Rationales Modify Async
    """
    modify_agent = factory.get_claim_modify_agent()

    tasks = [
        modify_agent.run_async(claim, rationale.rationale)
        for claim, rationale in zip(claims, rationales)
    ]
    claims: ClaimList = await asyncio.gather(*tasks, return_exceptions=True)
    claims: List[Claim] = add_uuid(claims)
    return claims


async def main(
    TOTAL_ITERATIONS: int,
    claim_load_basedir: str,
    statement_save_basedir: str,
):
    provider = factory.get_provider()

    # Claims 로드
    claims = sample_claims(claim_load_basedir)
    logger.info(f"[Done] Claims Loaded: {len(claims)}")

    edges = []
    instances = []
    final_claims = []

    instances.extend(claims)
    statement_graph = None

    try:
        for i in range(TOTAL_ITERATIONS):
            logger.info(f"[Iteration {i + 1} of {TOTAL_ITERATIONS}]")

            logger.info("[Start] Rationales Generation")
            rationales = await generate_rationales_async(claims, provider=provider)
            logger.info("[Done] Rationales Generated")

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

            logger.info(f"Rejected Rationales: {len(rejected_rationales)}")
            logger.info(f"Rejected Claims: {len(rejected_claims)}")

            if not rejected_rationales:
                logger.info("[Roop Done] No Rejected Rationales")
                break

            logger.info("[Start] Modified Rationales Generation")
            modified_claims = await generate_rationales_modify_async(
                rejected_claims, rejected_rationales
            )
            logger.info("[Done] Modified Rationales Generated")

            instances.extend(rationales)
            instances.extend(modified_claims)

            edges.extend(
                [(c.uuid, r.uuid) for c, r in zip(claims, rationales)],
            )
            edges.extend(
                [(r.uuid, c.uuid) for r, c in zip(rejected_rationales, modified_claims)]
            )

            claims = modified_claims

        logger.info("[Start] Statement Generation")
        statement: Statement = generate_statement(final_claims)
        logger.info("[Done] Statement Generated")
        instances.append(statement)

        logger.info("[Start] Statement Graph Generation")
        statement_graph: StatementGraph = generate_statement_graph(instances, edges)
        logger.info("[Done] Statement Graph Generated")

        savepath = os.path.join(
            statement_save_basedir, f"statement-{statement.uuid}.json"
        )

        save_json(statement_graph.to_dict(), savepath)
        logger.info("[Done] Statement Graph Saved")

    except Exception as e:
        logger.error(f"Error: {e}")
        raise e

    finally:
        # 무조건 실행: 쓰레드 풀 정리
        logger.info("[Cleanup] Shutting down threads")
        ReactAgent.shutdown()
        logger.info("[Cleanup] Thread shutdown completed")

    return statement_graph


if __name__ == "__main__":
    statement = asyncio.run(
        main(
            TOTAL_ITERATIONS=2,
            claim_load_basedir="database/claim",
            statement_save_basedir="database/statement",
        )
    )
