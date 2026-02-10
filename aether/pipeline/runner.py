import asyncio
import os
from aether import factory
from aether.agents.claim.schema import Claim
from aether.agents.statement.schema import Statement
from aether.agents.thesis.schema import Thesis
from aether.config import get_config
from aether.config import resolve_path
from aether.llm.react import ReactAgent
from aether.logger import get_logger
from aether.pipeline.claim import generate_claims
from aether.pipeline.claim import generate_claims_async
from aether.pipeline.clause import build_clause_graph
from aether.pipeline.clause import generate_sub_clause
from aether.pipeline.clause import load_clause_graph
from aether.pipeline.factor import run_factor_revision
from aether.pipeline.factor import run_factor_revision_async
from aether.pipeline.statement import generate_statement
from aether.pipeline.statement import generate_statement_graph
from aether.pipeline.statement import verify_claims_loop
from aether.pipeline.thesis import generate_thesis
from aether.pipeline.thesis import generate_thesis_async
from aether.utils import load_json
from aether.utils import save_json

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def sample_thesis(thesis_load_basedir: str) -> Thesis:
    files = [f for f in os.listdir(thesis_load_basedir) if f.endswith(".json")]
    filepath = os.path.join(thesis_load_basedir, files[0])
    thesis_dict = load_json(filepath)
    thesis = Thesis(**thesis_dict)
    return thesis


def sample_claims(claim_load_basedir: str) -> list[Claim]:
    files = [f for f in os.listdir(claim_load_basedir) if f.endswith(".json")]
    filepath = os.path.join(claim_load_basedir, files[0])
    claims_dict = load_json(filepath)
    claims = [Claim(**c) for c in claims_dict.values()]
    return claims


def sample_statement(statement_load_basedir: str) -> Statement:
    files = [f for f in os.listdir(statement_load_basedir) if f.endswith(".json")]
    filepath = os.path.join(statement_load_basedir, files[0])
    statement_graph = load_json(filepath)
    statement_str = list(statement_graph.values())[-1]["statement"]
    statement_uuid = list(statement_graph.values())[-1]["uuid"]
    statement = Statement(uuid=statement_uuid, statement=statement_str)
    return statement


def load_all_theses(thesis_load_basedir: str) -> list[Thesis]:
    files = [f for f in os.listdir(thesis_load_basedir) if f.endswith(".json")]
    theses = []
    for f in files:
        filepath = os.path.join(thesis_load_basedir, f)
        thesis_dict = load_json(filepath)
        theses.append(Thesis(**thesis_dict))
    return theses


def load_all_claim_sets(claim_load_basedir: str) -> list[list[Claim]]:
    files = [f for f in os.listdir(claim_load_basedir) if f.endswith(".json")]
    claim_sets = []
    for f in files:
        filepath = os.path.join(claim_load_basedir, f)
        claims_dict = load_json(filepath)
        claims = [Claim(**c) for c in claims_dict.values()]
        claim_sets.append(claims)
    return claim_sets


def load_all_statements(statement_load_basedir: str) -> list[Statement]:
    files = [f for f in os.listdir(statement_load_basedir) if f.endswith(".json")]
    statements = []
    for f in files:
        filepath = os.path.join(statement_load_basedir, f)
        statement_graph = load_json(filepath)
        statement_str = list(statement_graph.values())[-1]["statement"]
        statement_uuid = list(statement_graph.values())[-1]["uuid"]
        statements.append(Statement(uuid=statement_uuid, statement=statement_str))
    return statements


# ---------------------------------------------------------------------------
# Clause
# ---------------------------------------------------------------------------


def run_clause(
    version: str = "v0",
    clause_save_basedir: str = None,
):
    config = get_config()
    clause_save_basedir = clause_save_basedir or os.path.join(
        resolve_path(config.data.database_dir), "clause"
    )

    clause_graph = build_clause_graph(config)

    os.makedirs(clause_save_basedir, exist_ok=True)
    savepath = os.path.join(clause_save_basedir, f"clause-{version}.json")
    clause_graph.save(savepath)
    logger.info(f"Clause graph saved to {savepath}")
    return clause_graph


# ---------------------------------------------------------------------------
# Thesis
# ---------------------------------------------------------------------------


def run_thesis(
    clause_load_basedir: str = None,
    thesis_save_basedir: str = None,
    clause_version: str = "v0",
):
    config = get_config()
    db_dir = resolve_path(config.data.database_dir)
    clause_load_basedir = clause_load_basedir or os.path.join(db_dir, "clause")
    thesis_save_basedir = thesis_save_basedir or os.path.join(db_dir, "thesis")

    clause_graph = load_clause_graph(clause_load_basedir, version=clause_version)
    subclause = generate_sub_clause(clause_graph, config=config)

    thesis = generate_thesis(*subclause.clause_trees.values(), config=config)
    logger.info(f"Thesis generated: {thesis.thesis[:100]}...")

    os.makedirs(thesis_save_basedir, exist_ok=True)
    savepath = os.path.join(thesis_save_basedir, f"thesis-{thesis.uuid}.json")
    save_json(thesis.model_dump(), savepath)
    return thesis


async def run_thesis_parallel(
    clause_load_basedir: str = None,
    thesis_save_basedir: str = None,
    clause_version: str = "v0",
    num_parallel: int = 4,
):
    config = get_config()
    db_dir = resolve_path(config.data.database_dir)
    clause_load_basedir = clause_load_basedir or os.path.join(db_dir, "clause")
    thesis_save_basedir = thesis_save_basedir or os.path.join(db_dir, "thesis")

    clause_graph = load_clause_graph(clause_load_basedir, version=clause_version)
    semaphore = asyncio.Semaphore(config.pipeline.max_workers)

    subgraphs = [
        generate_sub_clause(clause_graph, config=config) for _ in range(num_parallel)
    ]
    completed = 0

    async def gen_one(subgraph):
        nonlocal completed
        async with semaphore:
            result = await generate_thesis_async(
                *subgraph.clause_trees.values(), config=config
            )
            completed += 1
            logger.info(f"Parallel thesis {completed}/{num_parallel} done")
            return result

    theses = await asyncio.gather(*[gen_one(sg) for sg in subgraphs])
    os.makedirs(thesis_save_basedir, exist_ok=True)

    for thesis in theses:
        savepath = os.path.join(thesis_save_basedir, f"thesis-{thesis.uuid}.json")
        save_json(thesis.model_dump(), savepath)
        logger.info(f"Thesis saved: {savepath}")

    return theses


# ---------------------------------------------------------------------------
# Claim
# ---------------------------------------------------------------------------


def run_claim(
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


async def run_claim_parallel(
    thesis_load_basedir: str = None,
    claim_save_basedir: str = None,
    num_parallel: int = 4,
):
    config = get_config()
    db_dir = resolve_path(config.data.database_dir)
    thesis_load_basedir = thesis_load_basedir or os.path.join(db_dir, "thesis")
    claim_save_basedir = claim_save_basedir or os.path.join(db_dir, "claim")

    semaphore = asyncio.Semaphore(config.pipeline.max_workers)

    theses = load_all_theses(thesis_load_basedir)[:num_parallel]
    logger.info(f"Processing {len(theses)} theses in parallel")
    completed = 0

    async def gen_one(thesis):
        nonlocal completed
        async with semaphore:
            result = thesis, await generate_claims_async(thesis, config=config)
            completed += 1
            logger.info(f"Parallel claim {completed}/{len(theses)} done")
            return result

    results = await asyncio.gather(*[gen_one(t) for t in theses])

    os.makedirs(claim_save_basedir, exist_ok=True)

    for thesis, claims in results:
        claims_dict = {c.uuid: c.model_dump() for c in claims}
        savepath = os.path.join(claim_save_basedir, f"claim-{thesis.uuid}.json")
        save_json(claims_dict, savepath)
        logger.info(f"Claims saved: {savepath}")

    return results


# ---------------------------------------------------------------------------
# Statement
# ---------------------------------------------------------------------------


async def run_statement(
    claim_load_basedir: str = None,
    statement_save_basedir: str = None,
):
    config = get_config()
    db_dir = resolve_path(config.data.database_dir)
    claim_load_basedir = claim_load_basedir or os.path.join(db_dir, "claim")
    statement_save_basedir = statement_save_basedir or os.path.join(db_dir, "statement")

    semaphore = asyncio.Semaphore(config.pipeline.max_workers)
    provider = factory.get_provider()

    claims = sample_claims(claim_load_basedir)
    logger.info(f"{len(claims)} claims loaded")

    try:
        final_claims, instances, edges = await verify_claims_loop(
            claims, provider=provider, semaphore=semaphore, config=config
        )

        # Add original claims to instances for graph
        instances = list(claims) + instances

        statement = generate_statement(final_claims, config=config)
        logger.info("Statement generated")
        instances.append(statement)

        statement_graph = generate_statement_graph(instances, edges)

        os.makedirs(statement_save_basedir, exist_ok=True)
        savepath = os.path.join(
            statement_save_basedir, f"statement-{statement.uuid}.json"
        )
        save_json(statement_graph.to_dict(), savepath)
        logger.info(f"Statement graph saved to {savepath}")

    except Exception as e:
        logger.error(f"Statement generation failed: {e}")
        raise e

    finally:
        ReactAgent.shutdown()

    return statement_graph


async def _process_one_statement(
    claims: list[Claim],
    provider,
    semaphore: asyncio.Semaphore,
    statement_save_basedir: str,
    config=None,
    counter: list = None,
    total: int = 0,
):
    try:
        final_claims, instances, edges = await verify_claims_loop(
            claims, provider=provider, semaphore=semaphore, config=config
        )

        instances = list(claims) + instances
        statement = generate_statement(final_claims, config=config)
        if counter is not None:
            counter[0] += 1
            logger.info(f"Parallel statement {counter[0]}/{total} done")
        else:
            logger.info("Statement generated")
        instances.append(statement)

        statement_graph = generate_statement_graph(instances, edges)

        savepath = os.path.join(
            statement_save_basedir, f"statement-{statement.uuid}.json"
        )
        save_json(statement_graph.to_dict(), savepath)
        logger.info(f"Statement graph saved to {savepath}")

        return statement_graph
    except Exception as e:
        logger.error(f"Statement processing failed: {type(e).__name__}: {e}")
        raise


async def run_statement_parallel(
    claim_load_basedir: str = None,
    statement_save_basedir: str = None,
    num_parallel: int = 4,
):
    config = get_config()
    db_dir = resolve_path(config.data.database_dir)
    claim_load_basedir = claim_load_basedir or os.path.join(db_dir, "claim")
    statement_save_basedir = statement_save_basedir or os.path.join(db_dir, "statement")

    semaphore = asyncio.Semaphore(config.pipeline.max_workers)
    provider = factory.get_provider()

    claim_sets = load_all_claim_sets(claim_load_basedir)[:num_parallel]
    logger.info(f"Processing {len(claim_sets)} claim sets in parallel")
    counter = [0]

    os.makedirs(statement_save_basedir, exist_ok=True)

    try:
        results = await asyncio.gather(
            *[
                _process_one_statement(
                    claims,
                    provider,
                    semaphore,
                    statement_save_basedir,
                    config=config,
                    counter=counter,
                    total=len(claim_sets),
                )
                for claims in claim_sets
            ]
        )
    finally:
        ReactAgent.shutdown()

    return results


# ---------------------------------------------------------------------------
# Factor
# ---------------------------------------------------------------------------


def run_factor(
    statement_load_basedir: str = None,
    factor_save_basedir: str = None,
):
    config = get_config()
    db_dir = resolve_path(config.data.database_dir)
    statement_load_basedir = statement_load_basedir or os.path.join(db_dir, "statement")
    factor_save_basedir = factor_save_basedir or os.path.join(db_dir, "factor")

    statement = sample_statement(statement_load_basedir)
    factor_statement, factor_code = run_factor_revision(statement, config=config)
    factor_dict = {**factor_statement.model_dump(), **factor_code.model_dump()}

    os.makedirs(factor_save_basedir, exist_ok=True)
    savepath = os.path.join(factor_save_basedir, f"factor-{factor_statement.uuid}.json")
    save_json(factor_dict, savepath)
    logger.info(f"Factor saved to {savepath}")
    return factor_code


async def run_factor_parallel(
    statement_load_basedir: str = None,
    factor_save_basedir: str = None,
    num_parallel: int = 4,
):
    config = get_config()
    db_dir = resolve_path(config.data.database_dir)
    statement_load_basedir = statement_load_basedir or os.path.join(db_dir, "statement")
    factor_save_basedir = factor_save_basedir or os.path.join(db_dir, "factor")

    semaphore = asyncio.Semaphore(config.pipeline.max_workers)

    statements = load_all_statements(statement_load_basedir)[:num_parallel]
    logger.info(f"Processing {len(statements)} statements in parallel")
    completed = 0

    async def gen_one(statement):
        nonlocal completed
        async with semaphore:
            result = await run_factor_revision_async(statement, config=config)
            completed += 1
            logger.info(f"Parallel factor {completed}/{len(statements)} done")
            return result

    results = await asyncio.gather(*[gen_one(s) for s in statements])

    os.makedirs(factor_save_basedir, exist_ok=True)

    for factor_statement, factor_code in results:
        factor_dict = {**factor_statement.model_dump(), **factor_code.model_dump()}
        savepath = os.path.join(
            factor_save_basedir, f"factor-{factor_statement.uuid}.json"
        )
        save_json(factor_dict, savepath)
        logger.info(f"Factor saved to {savepath}")

    return results
