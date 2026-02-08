from typing import Tuple
from aether import factory
from aether.agents.factor.schema import FactorCode
from aether.agents.factor.schema import FactorStatement
from aether.agents.factor.schema import ProofRevision
from aether.agents.statement.schema import Statement
from aether.config import Config
from aether.config import get_config
from aether.logger import get_logger
from aether.utils import generate_uuid

logger = get_logger(__name__)


def run_factor_revision(
    statement: Statement,
    config: Config = None,
) -> Tuple[FactorStatement, FactorCode]:
    """Run the factor generation pipeline: initial proof → revision loop → code generation.

    Returns:
        (factor_statement, factor_code) with UUIDs assigned.
    """
    config = config or get_config()

    factor_statement = generate_initial_factor_statement(statement, config=config)

    for i in range(config.pipeline.revision_iterations):
        revision = generate_proof_check(factor_statement, config=config)
        if revision.is_pass:
            logger.info(f"Proof passed at revision {i + 1}")
            break
        factor_statement = generate_fixed_factor_statement(
            factor_statement, revision, config=config
        )

    factor_statement.uuid = generate_uuid()
    factor_code = generate_factor_code(factor_statement, config=config)
    return factor_statement, factor_code


def generate_initial_factor_statement(
    statement: Statement,
    config: Config = None,
) -> FactorStatement:
    initial_factor_agent = factory.get_initial_factor_agent(config)
    initial_factor_statement = initial_factor_agent.run(statement.statement)
    return initial_factor_statement


def generate_proof_check(
    factor_statement: FactorStatement,
    config: Config = None,
) -> ProofRevision:
    proof_check_agent = factory.get_proof_check_agent(config)
    proof_revision = proof_check_agent.run(factor_statement.proof)
    return proof_revision


def generate_fixed_factor_statement(
    initial_factor_statement: FactorStatement,
    revision: ProofRevision,
    config: Config = None,
) -> FactorStatement:
    proof_fix_agent = factory.get_proof_fix_agent(config)
    fixed_factor_statement = proof_fix_agent.run(
        initial_factor_statement.proof, revision
    )
    return fixed_factor_statement


def generate_factor_code(
    factor_statement: FactorStatement,
    config: Config = None,
) -> FactorCode:
    factor_code_agent = factory.get_factor_code_agent(config)
    factor_code = factor_code_agent.run(factor_statement.proof)
    return factor_code
