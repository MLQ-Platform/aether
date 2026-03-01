import asyncio
import os
import random
from aether import factory
from aether.agents.claim.schema import Claim
from aether.agents.statement.schema import Statement
from aether.agents.thesis.schema import Thesis
from aether.config import get_config
from aether.config import resolve_path
from aether.exceptions import DataError
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
from aether.pipeline.statement import verify_claims_loop
from aether.pipeline.thesis import generate_thesis
from aether.pipeline.thesis import generate_thesis_async
from aether.utils import load_json
from aether.utils import save_json
from aether.utils import uuid_savepath

logger = get_logger(__name__)


def _parse_claims_payload(payload) -> list[Claim]:
    data = payload
    if isinstance(data, dict):
        if "claims" in data and isinstance(data["claims"], list):
            data = data["claims"]
        elif all(isinstance(v, dict) for v in data.values()):
            data = list(data.values())
    return [Claim(**c) for c in data]


def sample_thesis(thesis_load_basedir: str) -> tuple[Thesis, str]:
    files = [f for f in os.listdir(thesis_load_basedir) if f.endswith(".json")]
    if not files:
        raise DataError(f"No thesis JSON files found in {thesis_load_basedir}")
    filepath = os.path.join(thesis_load_basedir, random.choice(files))
    thesis_dict = load_json(filepath)
    thesis = Thesis(**thesis_dict)
    return thesis, os.path.basename(filepath)


def sample_claims(claim_load_basedir: str) -> tuple[list[Claim], str]:
    files = [f for f in os.listdir(claim_load_basedir) if f.endswith(".json")]
    if not files:
        raise DataError(f"No claim JSON files found in {claim_load_basedir}")
    filepath = os.path.join(claim_load_basedir, random.choice(files))
    claims = _parse_claims_payload(load_json(filepath))
    return claims, os.path.basename(filepath)


def sample_statement(statement_load_basedir: str) -> tuple[Statement, str]:
    files = [f for f in os.listdir(statement_load_basedir) if f.endswith(".json")]
    if not files:
        raise DataError(f"No statement JSON files found in {statement_load_basedir}")
    filepath = os.path.join(statement_load_basedir, random.choice(files))
    statement_data = load_json(filepath)
    return Statement(
        statement=statement_data["statement"]["statement"]
    ), os.path.basename(filepath)


def load_all_theses(thesis_load_basedir: str) -> list[tuple[Thesis, str]]:
    files = sorted(f for f in os.listdir(thesis_load_basedir) if f.endswith(".json"))
    theses: list[tuple[Thesis, str]] = []
    for f in files:
        filepath = os.path.join(thesis_load_basedir, f)
        thesis_dict = load_json(filepath)
        theses.append((Thesis(**thesis_dict), f))
    return theses


def load_all_claim_sets(claim_load_basedir: str) -> list[tuple[list[Claim], str]]:
    files = sorted(f for f in os.listdir(claim_load_basedir) if f.endswith(".json"))
    claim_sets: list[tuple[list[Claim], str]] = []
    for f in files:
        filepath = os.path.join(claim_load_basedir, f)
        claim_sets.append((_parse_claims_payload(load_json(filepath)), f))
    return claim_sets


def load_all_statements(statement_load_basedir: str) -> list[tuple[Statement, str]]:
    files = sorted(f for f in os.listdir(statement_load_basedir) if f.endswith(".json"))
    statements: list[tuple[Statement, str]] = []
    for f in files:
        filepath = os.path.join(statement_load_basedir, f)
        statement_data = load_json(filepath)
        statements.append(
            (Statement(statement=statement_data["statement"]["statement"]), f)
        )
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
    savepath = uuid_savepath(thesis_save_basedir, "thesis")
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
        savepath = uuid_savepath(thesis_save_basedir, "thesis")
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

    thesis, thesis_file = sample_thesis(thesis_load_basedir)
    claims = generate_claims(thesis, config=config)
    logger.info(f"{len(claims)} claims generated")

    os.makedirs(claim_save_basedir, exist_ok=True)
    savepath = uuid_savepath(claim_save_basedir, "claim")
    claim_record = {
        "source_file": thesis_file,
        "claims": [c.model_dump() for c in claims],
    }
    save_json(claim_record, savepath)
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

    async def gen_one(thesis_record):
        nonlocal completed
        thesis, thesis_file = thesis_record
        async with semaphore:
            result = thesis_file, await generate_claims_async(thesis, config=config)
            completed += 1
            logger.info(f"Parallel claim {completed}/{len(theses)} done")
            return result

    results = await asyncio.gather(*[gen_one(t) for t in theses])
    os.makedirs(claim_save_basedir, exist_ok=True)

    for thesis_file, claims in results:
        savepath = uuid_savepath(claim_save_basedir, "claim")
        claim_record = {
            "source_file": thesis_file,
            "claims": [c.model_dump() for c in claims],
        }
        save_json(claim_record, savepath)
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

    claims, claim_file = sample_claims(claim_load_basedir)
    logger.info(f"{len(claims)} claims loaded")

    try:
        final_claims, sequence = await verify_claims_loop(
            claims, provider=provider, semaphore=semaphore, config=config
        )

        statement = generate_statement(final_claims, config=config)
        logger.info("Statement generated")
        sequence.append({"type": "statement", "item": statement.model_dump()})
        statement_record = {
            "sequence": sequence,
            "statement": statement.model_dump(),
            "source_file": claim_file,
        }

        os.makedirs(statement_save_basedir, exist_ok=True)
        savepath = uuid_savepath(statement_save_basedir, "statement")
        save_json(statement_record, savepath)
        logger.info(f"Statement record saved to {savepath}")

    except Exception as e:
        logger.error(f"Statement generation failed: {e}")
        raise e

    finally:
        ReactAgent.shutdown()

    return statement_record


async def _process_one_statement(
    claims: list[Claim],
    source_claim_file: str | None,
    provider,
    semaphore: asyncio.Semaphore,
    statement_save_basedir: str,
    config=None,
    counter: list = None,
    total: int = 0,
):
    try:
        final_claims, sequence = await verify_claims_loop(
            claims, provider=provider, semaphore=semaphore, config=config
        )

        statement = generate_statement(final_claims, config=config)
        if counter is not None:
            counter[0] += 1
            logger.info(f"Parallel statement {counter[0]}/{total} done")
        else:
            logger.info("Statement generated")
        sequence.append({"type": "statement", "item": statement.model_dump()})
        statement_record = {
            "sequence": sequence,
            "statement": statement.model_dump(),
            "source_file": source_claim_file,
        }

        savepath = uuid_savepath(statement_save_basedir, "statement")
        save_json(statement_record, savepath)
        logger.info(f"Statement record saved to {savepath}")

        return statement_record
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
                    source_claim_file,
                    provider,
                    semaphore,
                    statement_save_basedir,
                    config=config,
                    counter=counter,
                    total=len(claim_sets),
                )
                for claims, source_claim_file in claim_sets
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

    statement, statement_file = sample_statement(statement_load_basedir)
    factor_statement, factor_code = run_factor_revision(statement, config=config)
    factor_dict = {
        **factor_statement.model_dump(),
        **factor_code.model_dump(),
        "source_file": statement_file,
    }

    os.makedirs(factor_save_basedir, exist_ok=True)
    savepath = uuid_savepath(factor_save_basedir, "factor")
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

    async def gen_one(statement_record):
        nonlocal completed
        statement, statement_file = statement_record
        async with semaphore:
            result = await run_factor_revision_async(statement, config=config)
            completed += 1
            logger.info(f"Parallel factor {completed}/{len(statements)} done")
            return statement_file, result

    results = await asyncio.gather(*[gen_one(s) for s in statements])

    os.makedirs(factor_save_basedir, exist_ok=True)

    for statement_file, (factor_statement, factor_code) in results:
        factor_dict = {
            **factor_statement.model_dump(),
            **factor_code.model_dump(),
            "source_file": statement_file,
        }
        savepath = uuid_savepath(factor_save_basedir, "factor")
        save_json(factor_dict, savepath)
        logger.info(f"Factor saved to {savepath}")

    return results


# ---------------------------------------------------------------------------
# Backtest
# ---------------------------------------------------------------------------


def run_backtest_batch(
    factor_dir: str | None = None,
    backtest_save_basedir: str | None = None,
):
    config = get_config()
    db_dir = resolve_path(config.data.database_dir)
    factor_dir = factor_dir or os.path.join(db_dir, "factor")
    backtest_save_basedir = backtest_save_basedir or os.path.join(db_dir, "backtest")

    from aether.pipeline.backtest import run_batch_factor_backtests

    summary = run_batch_factor_backtests(
        factor_dir=factor_dir,
        backtest_dir=backtest_save_basedir,
    )
    logger.info(
        "Backtest batch done: "
        f"processed={summary['processed']}, skipped={summary['skipped_existing']}, failed={summary['failed']}"
    )
    return summary
