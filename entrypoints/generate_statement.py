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
from aether.agents.thesis.schema import Thesis
from aether.clause.graph import ClauseGraph
from aether.clause.tree.base import ClauseTree
from aether.provider import InMemoryDataProvider
from aether.utils import add_uuid
from aether.utils import generate_uuid


def load_clause_graph(filepath: str) -> ClauseGraph:
    clause_graph = ClauseGraph.load(filepath)
    return clause_graph


def generate_sub_clause(clause_graph: ClauseGraph) -> ClauseGraph:
    from aether.clause.graph.extractor import SubgraphExtractor

    extractor = SubgraphExtractor(clause_graph)
    subgraph = extractor.extract(size=2)
    return subgraph


def generate_thesis(tree_a: ClauseTree, tree_b: ClauseTree) -> Thesis:
    thesis_agent = factory.get_thesis_agent()
    thesis = thesis_agent.run(tree_a, tree_b)
    thesis.uuid = generate_uuid()
    return thesis


def generate_claims(thesis: Thesis) -> List[Claim]:
    claim_agent = factory.get_claim_agent()
    claims = claim_agent.run(thesis.thesis)
    claims = add_uuid(claims.claims)
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
    tasks = [
        rationale_agent.run_async(claim, exec_context=exec_context) for claim in claims
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


async def main(TOTAL_ITERATIONS: int = 4, graph_filepath: str = "clause-graph-v1.json"):
    provider = factory.get_provider()

    # Clause Graph 로드
    clause = load_clause_graph(graph_filepath)
    # Clause Graph에서 Sub-Clause 추출
    subclause = generate_sub_clause(clause)
    # Thesis 생성
    thesis = generate_thesis(*subclause.clause_trees.values())
    # Thesis로 Claim 생성
    claims = generate_claims(thesis)

    print(f"Generated Claims: {len(claims)}")

    edges = []
    instances = []
    final_claims = []

    instances.append(thesis)
    instances.extend(claims)
    edges.extend([(thesis.uuid, c.uuid) for c in claims])

    for i in range(TOTAL_ITERATIONS):
        print(f"Iteration {i + 1} of {TOTAL_ITERATIONS}")

        rationales = await generate_rationales_async(claims, provider=provider)

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

        print(
            f"Rejected Rationales & Claims: {len(rejected_rationales)} & {len(rejected_claims)}"
        )

        if not rejected_rationales:
            break

        modified_claims = await generate_rationales_modify_async(
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

    statement: Statement = generate_statement(final_claims)
    instances.append(statement)
    statement_graph: StatementGraph = generate_statement_graph(instances, edges)
    return statement_graph


if __name__ == "__main__":
    statement = asyncio.run(main())
