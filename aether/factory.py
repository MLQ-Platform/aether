from aether.config import Config
from aether.config import get_config
from aether.provider import InMemoryDataProvider


def get_provider():
    provider = InMemoryDataProvider()
    return provider


def get_clause_generator(provider: InMemoryDataProvider, config: Config = None):
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
    return client


def get_thesis_agent(config: Config = None):
    from aether.agents import ThesisRevealingAgent

    config = config or get_config()
    client = get_client(config)

    thesis_agent = ThesisRevealingAgent(
        model=config.llm.model,
        client=client,
        system_promt_path="thesis-revealing.txt",
    )
    return thesis_agent


def get_claim_agent(config: Config = None):
    from aether.agents import ClaimDecompositionAgent

    config = config or get_config()
    client = get_client(config)

    claim_agent = ClaimDecompositionAgent(
        model=config.llm.model,
        client=client,
        system_promt_path="statement-claim.txt",
    )
    return claim_agent


def get_statement_agent(config: Config = None):
    from aether.agents import StatementAgent

    config = config or get_config()
    client = get_client(config)

    statement_agent = StatementAgent(
        model=config.llm.model,
        client=client,
        system_promt_path="statement-final.txt",
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
    )
    return claim_modify_agent


def get_initial_factor_agent(config: Config = None):
    from aether.agents import InitialFactorStatementAgent

    config = config or get_config()
    client = get_client(config)

    initial_factor_agent = InitialFactorStatementAgent(
        model=config.llm.model,
        client=client,
    )
    return initial_factor_agent


def get_proof_check_agent(config: Config = None):
    from aether.agents import ProofCheckAgent

    config = config or get_config()
    client = get_client(config)

    proof_check_agent = ProofCheckAgent(
        model=config.llm.model,
        client=client,
    )
    return proof_check_agent


def get_proof_fix_agent(config: Config = None):
    from aether.agents import ProofFixAgent

    config = config or get_config()
    client = get_client(config)

    proof_fix_agent = ProofFixAgent(
        model=config.llm.model,
        client=client,
    )
    return proof_fix_agent


def get_factor_code_agent(config: Config = None):
    from aether.agents import FactorCodeAgent

    config = config or get_config()
    client = get_client(config)

    factor_code_agent = FactorCodeAgent(
        model=config.llm.model,
        client=client,
    )
    return factor_code_agent


# --- Async factory functions ---


def get_async_thesis_agent(config: Config = None):
    from aether.agents import ThesisRevealingAgent

    config = config or get_config()
    client = get_async_client(config)

    thesis_agent = ThesisRevealingAgent(
        model=config.llm.model,
        client=client,
        system_promt_path="thesis-revealing.txt",
    )
    return thesis_agent


def get_async_claim_agent(config: Config = None):
    from aether.agents import ClaimDecompositionAgent

    config = config or get_config()
    client = get_async_client(config)

    claim_agent = ClaimDecompositionAgent(
        model=config.llm.model,
        client=client,
        system_promt_path="statement-claim.txt",
    )
    return claim_agent


def get_async_statement_agent(config: Config = None):
    from aether.agents import StatementAgent

    config = config or get_config()
    client = get_async_client(config)

    statement_agent = StatementAgent(
        model=config.llm.model,
        client=client,
        system_promt_path="statement-final.txt",
    )
    return statement_agent


def get_async_initial_factor_agent(config: Config = None):
    from aether.agents import InitialFactorStatementAgent

    config = config or get_config()
    client = get_async_client(config)

    initial_factor_agent = InitialFactorStatementAgent(
        model=config.llm.model,
        client=client,
    )
    return initial_factor_agent


def get_async_proof_check_agent(config: Config = None):
    from aether.agents import ProofCheckAgent

    config = config or get_config()
    client = get_async_client(config)

    proof_check_agent = ProofCheckAgent(
        model=config.llm.model,
        client=client,
    )
    return proof_check_agent


def get_async_proof_fix_agent(config: Config = None):
    from aether.agents import ProofFixAgent

    config = config or get_config()
    client = get_async_client(config)

    proof_fix_agent = ProofFixAgent(
        model=config.llm.model,
        client=client,
    )
    return proof_fix_agent


def get_async_factor_code_agent(config: Config = None):
    from aether.agents import FactorCodeAgent

    config = config or get_config()
    client = get_async_client(config)

    factor_code_agent = FactorCodeAgent(
        model=config.llm.model,
        client=client,
    )
    return factor_code_agent


def get_nodes(provider: InMemoryDataProvider, config: Config = None) -> list:
    from aether.clause import nodes

    config = config or get_config()
    P = config.clause.period
    END_DATE = config.data.end_date
    TICKER = config.data.ticker

    NODES = [
        # Basic math operation nodes
        nodes.ADD(),
        nodes.DIV(),
        nodes.SUB(),
        nodes.ABS(),
        nodes.SMA(period=P),
        nodes.SHIFT(period=P),
        nodes.DIFF(period=P),
        nodes.PctChange(period=P),
        nodes.STD(period=P),
        nodes.NewHigh(period=P),
        nodes.NewLow(period=P),
        nodes.MAX(period=P),
        nodes.MIN(period=P),
        nodes.ZSCORE(period=P),
        nodes.SKEW(period=P),
        nodes.KURT(period=P),
        nodes.ZEXP(period=P),
        nodes.ZSigmoid(period=P),
        # Root nodes
        nodes.CrossUp(),
        nodes.CrossDown(),
        nodes.Comparison(),
        nodes.ZBetween(period=P, lo=-1.5, hi=1.5),
        nodes.EqualApprox(tol=1e-2),
        nodes.UpStreak(period=P),
        nodes.DownStreak(period=P),
        nodes.MeanRevertKick(period=P, z_th=1.0, dmax=P, eps=0.01),
        nodes.PullbackWithinBand(period=P, k=0.5),
        nodes.DrawdownExceed(pct=0.1, lookback=P),
        nodes.JumpDetect(period=P, q_tail=0.1),
        # Data nodes
        nodes.DATA(
            label="OPEN",
            ticker=TICKER,
            provider=provider,
            end_date=END_DATE,
        ),
        nodes.DATA(
            label="HIGH",
            ticker=TICKER,
            provider=provider,
            end_date=END_DATE,
        ),
        nodes.DATA(
            label="LOW",
            ticker=TICKER,
            provider=provider,
            end_date=END_DATE,
        ),
        nodes.DATA(
            label="CLOSE",
            ticker=TICKER,
            provider=provider,
            end_date=END_DATE,
        ),
        nodes.DATA(
            label="VOLUME",
            ticker=TICKER,
            provider=provider,
            end_date=END_DATE,
        ),
        nodes.DATA(
            label="PREMIUM_INDEX_CLOSE",
            ticker=TICKER,
            provider=provider,
            end_date=END_DATE,
        ),
        nodes.DATA(
            label="PREMIUM_INDEX_OPEN",
            ticker=TICKER,
            provider=provider,
            end_date=END_DATE,
        ),
        nodes.DATA(
            label="PREMIUM_INDEX_HIGH",
            ticker=TICKER,
            provider=provider,
            end_date=END_DATE,
        ),
        nodes.DATA(
            label="PREMIUM_INDEX_LOW",
            ticker=TICKER,
            provider=provider,
            end_date=END_DATE,
        ),
        nodes.DATA(
            label="TAKER_BUY_VOLUME",
            ticker=TICKER,
            provider=provider,
            end_date=END_DATE,
        ),
        nodes.DATA(
            label="TAKER_SELL_VOLUME",
            ticker=TICKER,
            provider=provider,
            end_date=END_DATE,
        ),
        nodes.DATA(
            label="FUNDING_SCORE",
            ticker=TICKER,
            provider=provider,
            end_date=END_DATE,
        ),
        nodes.DATA(
            label="ORDER_FLOW_IMBALANCE",
            ticker=TICKER,
            provider=provider,
            end_date=END_DATE,
        ),
    ]

    return NODES
