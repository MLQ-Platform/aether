from aether import factory
from aether.agents.factor.schema import FactorCode
from aether.agents.factor.schema import FactorStatement
from aether.agents.factor.schema import ProofRevision
from aether.agents.statement.schema import Statement


def sample_statement() -> Statement: ...


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


def main(REVISION_ITER=3):
    statement = sample_statement()

    factor_statement = generate_initial_factor_statement(statement)

    for _ in range(REVISION_ITER):
        revision = generate_proof_check(factor_statement)

        if revision.is_pass:
            break

        factor_statement = generate_fiexd_fator_statement(factor_statement, revision)

    factor_code = generate_factor_code(factor_statement)
    return factor_code


if __name__ == "__main__":
    factor_code = main()
    print(factor_code)
