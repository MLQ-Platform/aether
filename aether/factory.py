from aether.config import Config
from aether.config import get_config
from aether.provider import InMemoryDataProvider

_async_clients: list = []


def get_provider():
    provider = InMemoryDataProvider()
    return provider


def get_clause_generator(provider: InMemoryDataProvider, config: Config = None):
    from aether.clause.nodes.registry import get_nodes
    from aether.clause.tree.generator import ClauseGenerator

    nodes = get_nodes(provider, config)
    generator = ClauseGenerator(nodes)
    return generator


def get_client(config: Config = None):
    from openai import OpenAI

    config = config or get_config()

    client = OpenAI(
        base_url=config.llm.base_url,
        api_key=config.llm.api_key,
        timeout=config.llm.timeout,
        max_retries=config.llm.max_retries,
    )
    return client


def get_async_client(config: Config = None):
    from openai import AsyncOpenAI

    config = config or get_config()

    client = AsyncOpenAI(
        base_url=config.llm.base_url,
        api_key=config.llm.api_key,
        timeout=config.llm.timeout,
        max_retries=config.llm.max_retries,
    )
    _async_clients.append(client)
    return client


async def cleanup_async_clients():
    """Close all tracked AsyncOpenAI clients to prevent 'Event loop is closed' errors."""
    for client in _async_clients:
        await client.close()
    _async_clients.clear()


def get_thesis_agent(config: Config = None, *, async_: bool = False):
    from aether.agents import ThesisRevealingAgent

    config = config or get_config()
    client = get_async_client(config) if async_ else get_client(config)

    thesis_agent = ThesisRevealingAgent(
        model=config.llm.model,
        client=client,
        system_promt_path="thesis-revealing.txt",
        max_retries=config.llm.parse_retries,
    )
    return thesis_agent


def get_claim_agent(config: Config = None, *, async_: bool = False):
    from aether.agents import ClaimDecompositionAgent

    config = config or get_config()
    client = get_async_client(config) if async_ else get_client(config)

    claim_agent = ClaimDecompositionAgent(
        model=config.llm.model,
        client=client,
        system_promt_path="statement-claim.txt",
        max_retries=config.llm.parse_retries,
    )
    return claim_agent


def get_statement_agent(config: Config = None, *, async_: bool = False):
    from aether.agents import StatementAgent

    config = config or get_config()
    client = get_async_client(config) if async_ else get_client(config)

    statement_agent = StatementAgent(
        model=config.llm.model,
        client=client,
        system_promt_path="statement-final.txt",
        max_retries=config.llm.parse_retries,
    )
    return statement_agent


def get_rationale_agent(config: Config = None):
    from aether.agents import RationaleAgent
    from aether.agents.rationale.tools import tools

    config = config or get_config()
    client = get_async_client(config)

    rationale_agent = RationaleAgent(
        model=config.llm.model,
        client=client,
        tools=tools,
        system_promt_path="statement-rationale.txt",
        max_iterations=config.agent.react_max_iterations,
        parse_retries=config.llm.parse_retries,
    )
    return rationale_agent


def get_claim_modify_agent(config: Config = None):
    from aether.agents import ClaimModifyAgent

    config = config or get_config()
    client = get_async_client(config)

    claim_modify_agent = ClaimModifyAgent(
        model=config.llm.model,
        client=client,
        system_promt_path="statement-claim-modify.txt",
        max_retries=config.llm.parse_retries,
    )
    return claim_modify_agent


def get_initial_factor_agent(config: Config = None, *, async_: bool = False):
    from aether.agents import InitialFactorStatementAgent

    config = config or get_config()
    client = get_async_client(config) if async_ else get_client(config)

    initial_factor_agent = InitialFactorStatementAgent(
        model=config.llm.model,
        client=client,
        max_retries=config.llm.parse_retries,
    )
    return initial_factor_agent


def get_proof_check_agent(config: Config = None, *, async_: bool = False):
    from aether.agents import ProofCheckAgent

    config = config or get_config()
    client = get_async_client(config) if async_ else get_client(config)

    proof_check_agent = ProofCheckAgent(
        model=config.llm.model,
        client=client,
        max_retries=config.llm.parse_retries,
    )
    return proof_check_agent


def get_proof_fix_agent(config: Config = None, *, async_: bool = False):
    from aether.agents import ProofFixAgent

    config = config or get_config()
    client = get_async_client(config) if async_ else get_client(config)

    proof_fix_agent = ProofFixAgent(
        model=config.llm.model,
        client=client,
        max_retries=config.llm.parse_retries,
    )
    return proof_fix_agent


def get_factor_code_agent(config: Config = None, *, async_: bool = False):
    from aether.agents import FactorCodeAgent

    config = config or get_config()
    client = get_async_client(config) if async_ else get_client(config)

    factor_code_agent = FactorCodeAgent(
        model=config.llm.model,
        client=client,
        max_retries=config.llm.parse_retries,
    )
    return factor_code_agent
