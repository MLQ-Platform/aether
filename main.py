import asyncio
import os
import time
from typing import List
from typing import Tuple
from pydantic import BaseModel
from aether.agents.claim.schema import Claim
from aether.agents.claim.schema import ClaimList
from aether.agents.rationale.schema import Rationale
from aether.agents.statement.graph import StatementGraph
from aether.agents.statement.graph.node import Node
from aether.agents.statement.schema import Statement
from aether.agents.thesis.schema import Thesis
from aether.utils import add_uuid


def get_statement_graph(
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


def get_client():
    """
    Get OpenAI client
    """
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv(dotenv_path="config/.env")

    API_KEY = os.getenv("OPENROUTER_API_KEY")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY,
    )
    return client


def get_async_client():
    """
    Get AsyncOpenAI client for async operations
    """
    from dotenv import load_dotenv
    from openai import AsyncOpenAI

    load_dotenv(dotenv_path="config/.env")

    API_KEY = os.getenv("OPENROUTER_API_KEY")

    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY,
    )
    return client


def get_thesis():
    thesis = Thesis(
        uuid="49d72f07",
        thesis="In trending markets with persistent directional moves, the relationship between consecutive upward streaks in absolute opening price skewness and downward streaks in smoothed low price skewness reveals a momentum-driven asymmetry in price distribution behavior. When opening prices exhibit sustained positive skewness streaks, indicating consistent gap-up behavior with right-tailed distributions, this statistically coincides with extended periods where low price skewness remains negatively skewed after smoothing, suggesting persistent selling pressure at daily lows. This dependency emerges from momentum regimes where bullish opening gaps create distribution asymmetries that are mirrored by bearish intraday pressure patterns, revealing that sustained directional moves in one price component's distribution tend to precede or accompany opposite distributional tendencies in another price component. Markets exhibiting this pattern are likely experiencing strong directional momentum where opening optimism contrasts with persistent intraday weakness, creating predictable distribution asymmetries across different price dimensions.",
    )

    return thesis


def get_claims(thesis: Thesis) -> ClaimList:
    from aether.agents.claim import ClaimDecompositionAgent

    client = get_client()

    claim_agent = ClaimDecompositionAgent(
        model="deepseek/deepseek-v3.2-exp",
        client=client,
    )

    result = claim_agent.run(thesis.thesis)

    print(f"[Claim Decomposition] {len(result.claims)} claims decomposed")
    return result


def get_statement(statement_graph: StatementGraph) -> Statement:
    from aether.agents.statement import StatementAgent

    client = get_client()

    final_claims = get_final_claims(statement_graph)

    statement_agent = StatementAgent(
        model="deepseek/deepseek-v3.2-exp",
        client=client,
    )

    statement = statement_agent.run(final_claims)
    return statement


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


def get_claims_mock(thesis: Thesis) -> List[Claim]:
    claims = ClaimList(
        claims=[
            Claim(
                claim="In trending markets with persistent directional moves, opening prices exhibit sustained positive skewness streaks indicating consistent gap-up behavior",
                condition="streak_length(skew(OPEN, 20) > 0) >= 3",
                data_columns=["OPEN"],
                verification_plan="Calculate 20-period rolling skewness of OPEN prices and identify consecutive periods where skewness > 0. Perform binomial test against random baseline to determine if streak lengths exceed chance expectation. Use permutation test (1000 shuffles) to compare observed streak distribution against random time series.",
            ),
            Claim(
                claim="In trending markets with persistent directional moves, smoothed low price skewness exhibits sustained negative skewness streaks indicating persistent selling pressure at daily lows",
                condition="streak_length(skew(rolling(LOW, 5), 20) < 0) >= 3",
                data_columns=["LOW"],
                verification_plan="Calculate 5-period smoothed LOW prices, then compute 20-period rolling skewness. Identify consecutive periods where smoothed LOW skewness < 0. Perform binomial test against random baseline and permutation test to assess if negative skewness streaks occur more frequently than expected by chance.",
            ),
            Claim(
                claim="In trending markets, upward streaks in opening price skewness statistically coincide with downward streaks in smoothed low price skewness",
                condition="corr(streak_indicator(skew(OPEN, 20) > 0), streak_indicator(skew(rolling(LOW, 5), 20) < 0)) > 0.3",
                data_columns=["OPEN", "LOW"],
                verification_plan="Create binary indicators for upward opening skewness streaks and downward smoothed low skewness streaks. Calculate Pearson correlation between these indicators. Perform correlation test with null hypothesis r=0 and use permutation test to compare observed correlation against random time-shifted baseline.",
            ),
            Claim(
                claim="The dependency between opening price skewness streaks and smoothed low price skewness streaks is stronger in momentum regimes than in non-trending periods",
                condition="corr(streak_indicator(skew(OPEN, 20) > 0), streak_indicator(skew(rolling(LOW, 5), 20) < 0))_trending > corr(streak_indicator(skew(OPEN, 20) > 0), streak_indicator(skew(rolling(LOW, 5), 20) < 0))_non_trending + 0.2",
                data_columns=["OPEN", "LOW", "CLOSE"],
                verification_plan="Define trending periods using ADX(14) > 25 and non-trending periods using ADX(14) < 20. Calculate correlation between skewness streak indicators separately for each regime. Perform two-sample t-test comparing correlation coefficients between regimes. Use bootstrap confidence intervals to assess significance of the difference.",
            ),
            Claim(
                claim="Sustained directional moves in opening price distribution precede opposite distributional tendencies in smoothed low price distribution",
                condition="cross_corr(streak_indicator(skew(OPEN, 20) > 0), streak_indicator(skew(rolling(LOW, 5), 20) < 0), lag=0) > cross_corr(streak_indicator(skew(OPEN, 20) > 0), streak_indicator(skew(rolling(LOW, 5), 20) < 0), lag=1)",
                data_columns=["OPEN", "LOW"],
                verification_plan="Calculate cross-correlation between opening skewness streak indicators and smoothed low skewness streak indicators at lag 0 and lag 1. Perform paired t-test comparing contemporaneous vs lagged correlations. Use Granger causality test to determine if opening skewness streaks predict subsequent low price skewness streaks.",
            ),
        ]
    )

    claims = add_uuid(claims.claims)
    return claims


async def get_raitionales_async(claims: ClaimList) -> List[Rationale]:
    """
    Process multiple claims concurrently using async RationaleAgent

    Args:
        claims: List of claims to process

    Returns:
        List of Rationale objects (same order as input claims)
    """
    from aether.agents.rationale import RationaleAgent
    from aether.llm.agent import registry

    client = get_async_client()
    tools = registry.get_tools(agent_name="rationale")

    rationale_agent = RationaleAgent(
        model="deepseek/deepseek-v3.2-exp",
        client=client,
        tools=tools,
        system_promt_path="statement-rationale.txt",
        use_async=True,  # Enable async mode
        verbose=True,
        max_iterations=5,
    )

    # Process all claims concurrently
    tasks = [rationale_agent.run_async(claim, to_schema=True) for claim in claims]
    rationales = await asyncio.gather(*tasks, return_exceptions=True)
    rationales = add_uuid(rationales)
    return rationales


async def get_rationales_modify_async(
    claims: ClaimList, rationales: List[Rationale]
) -> List[Claim]:
    from aether.agents.modify import ClaimModifyAgent

    client = get_async_client()

    modify_agent = ClaimModifyAgent(
        model="deepseek/deepseek-v3.2-exp",
        client=client,
        system_promt_path="statement-claim-modify.txt",
    )

    tasks = [
        modify_agent.run_async(claim, rationale.rationale)
        for claim, rationale in zip(claims, rationales)
    ]
    claims: ClaimList = await asyncio.gather(*tasks, return_exceptions=True)
    claims: List[Claim] = add_uuid(claims)
    return claims


async def main(TOTAL_ITERATIONS: int = 4):
    start = time.time()
    thesis = get_thesis()
    claims = get_claims_mock(thesis)

    edges = []
    instances = []

    instances.append(thesis)
    instances.extend(claims)

    edges.extend([(thesis.uuid, c.uuid) for c in claims])

    for i in range(TOTAL_ITERATIONS):
        print(f"Iteration {i + 1} of {TOTAL_ITERATIONS}")

        rationales = await get_raitionales_async(claims)

        rejected_rationales = [
            x[1] for x in zip(claims, rationales) if not x[1].is_accepted
        ]
        rejected_claims = [
            x[0] for x in zip(claims, rationales) if not x[1].is_accepted
        ]

        print(
            f"Rejected Rationales & Claims: {len(rejected_rationales)} & {len(rejected_claims)}"
        )

        if not rejected_rationales:
            break

        modified_claims = await get_rationales_modify_async(
            rejected_claims, rejected_rationales
        )

        instances.extend(rationales)
        instances.extend(modified_claims)

        edges.extend(
            [(c.uuid, r.uuid) for c, r in zip(claims, rationales)],
        )
        edges.extend(
            [(r.uuid, c.uuid) for r, c in zip(rejected_rationales, modified_claims)]
        )

        claims = modified_claims

    statement_graph = get_statement_graph(instances, edges)
    statement: Statement = get_statement(statement_graph)

    end = time.time()
    print(f"Time taken: {end - start} seconds")
    return statement


if __name__ == "__main__":
    statement = asyncio.run(main())
    print(f"[Done] {len(statement.nodes)} nodes")
