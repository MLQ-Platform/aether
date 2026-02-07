import os
from aether import factory
from aether.agents.factor.schema import FactorCode
from aether.agents.factor.schema import FactorStatement
from aether.agents.factor.schema import ProofRevision
from aether.agents.statement.schema import Statement
from aether.logger import get_logger
from aether.utils import generate_uuid
from aether.utils import load_json
from aether.utils import save_json

logger = get_logger(__name__)


def sample_statement(statement_load_basedir: str) -> Statement:
    files = [f for f in os.listdir(statement_load_basedir) if f.endswith(".json")]
    filepath = os.path.join(statement_load_basedir, files[0])
    statement_graph = load_json(filepath)
    statement_str = list(statement_graph.values())[-1]["statement"]
    statement_uuid = list(statement_graph.values())[-1]["uuid"]
    statement = Statement(uuid=statement_uuid, statement=statement_str)
    return statement


def generate_initial_factor_statement(statement: Statement) -> FactorStatement:
    initial_factor_agent = factory.get_initial_factor_agent()
    initial_factor_statement = initial_factor_agent.run(statement.statement)
    return initial_factor_statement


def generate_proof_check(factor_statement: FactorStatement) -> ProofRevision:
    proof_check_agent = factory.get_proof_check_agent()
    proof_revision = proof_check_agent.run(factor_statement.proof)
    return proof_revision


def generate_fiexd_fator_statement(
    initial_factor_statement: FactorStatement, revision: ProofRevision
) -> FactorStatement:
    proof_fix_agent = factory.get_proof_fix_agent()
    fixed_factor_statement = proof_fix_agent.run(
        initial_factor_statement.proof, revision
    )
    return fixed_factor_statement


def generate_factor_code(factor_statement: FactorStatement) -> FactorCode:
    factor_code_agent = factory.get_factor_code_agent()
    factor_code = factor_code_agent.run(factor_statement.proof)
    return factor_code


def main(
    REVISION_ITER=3,
    statement_load_basedir: str = "database/statement",
    factor_save_basedir: str = "database/factor",
):
    logger.info(f"[Param] Revision Iter: {REVISION_ITER}")

    statement = sample_statement(statement_load_basedir)
    logger.info(f"[Done] Sample Statement: {statement.statement}")

    factor_statement = generate_initial_factor_statement(statement)
    logger.info("[Done] Generate Initial Factor Statement")

    for _ in range(REVISION_ITER):
        logger.info(f"[Iteration {_ + 1} of {REVISION_ITER}]")
        revision = generate_proof_check(factor_statement)
        logger.info("[Done] Generate Proof Check")

        if revision.is_pass:
            logger.info("[Done] No Revision Needed")
            break

        factor_statement = generate_fiexd_fator_statement(factor_statement, revision)
        logger.info("[Done] Generate Fixed Factor Statement")

    factor_statement.uuid = generate_uuid()
    factor_code = generate_factor_code(factor_statement)
    factor_dict = {**factor_statement.model_dump(), **factor_code.model_dump()}

    savepath = os.path.join(factor_save_basedir, f"factor-{factor_statement.uuid}.json")
    save_json(factor_dict, savepath)
    logger.info("[Done] Generate Factor Code")
    return factor_code


if __name__ == "__main__":
    factor_code = main(
        REVISION_ITER=3,
        statement_load_basedir="database/statement",
        factor_save_basedir="database/factor",
    )
