from aether.config import Config
from aether.provider import InMemoryDataProvider


def get_provider():
    provider = InMemoryDataProvider()
    return provider


def get_clause_generator(provider: InMemoryDataProvider):
    from aether.clause.tree.generator import ClauseGenerator

    nodes = get_nodes(provider)
    generator = ClauseGenerator(nodes)
    return generator


def get_client():
    from openai import OpenAI

    config = Config()

    client = OpenAI(
        base_url=config.BASE_URL,
        api_key=config.API_KEY,
    )
    return client


def get_async_client():
    from openai import AsyncOpenAI

    config = Config()

    client = AsyncOpenAI(
        base_url=config.BASE_URL,
        api_key=config.API_KEY,
    )
    return client


def get_thesis_agent(model_name="deepseek/deepseek-v3.2-exp"):
    from aether.agents import ThesisRevealingAgent

    client = get_client()

    thesis_agent = ThesisRevealingAgent(
        model=model_name,
        client=client,
        system_promt_path="thesis-revealing.txt",
    )
    return thesis_agent


def get_claim_agent(model_name="deepseek/deepseek-v3.2-exp"):
    from aether.agents import ClaimDecompositionAgent

    client = get_client()

    claim_agent = ClaimDecompositionAgent(
        model=model_name,
        client=client,
        system_promt_path="statement-claim.txt",
    )
    return claim_agent


def get_statement_agent(model_name="deepseek/deepseek-v3.2-exp"):
    from aether.agents import StatementAgent

    client = get_client()

    statement_agent = StatementAgent(
        model=model_name,
        client=client,
        system_promt_path="statement-final.txt",
    )
    return statement_agent


def get_rationale_agent(model_name="deepseek/deepseek-v3.2-exp"):
    from aether.agents import RationaleAgent
    from aether.agents.rationale.tools import tools

    client = get_async_client()

    rationale_agent = RationaleAgent(
        model=model_name,
        client=client,
        tools=tools,
        system_promt_path="statement-rationale.txt",
        max_iterations=10,
    )
    return rationale_agent


def get_claim_modify_agent(model_name="deepseek/deepseek-v3.2-exp"):
    from aether.agents import ClaimModifyAgent

    client = get_async_client()

    claim_modify_agent = ClaimModifyAgent(
        model=model_name,
        client=client,
        system_promt_path="statement-claim-modify.txt",
    )
    return claim_modify_agent


def get_initial_factor_agent(model_name="deepseek/deepseek-v3.2-exp"):
    from aether.agents import InitialFactorStatementAgent

    client = get_client()

    initial_factor_agent = InitialFactorStatementAgent(
        model=model_name,
        client=client,
    )
    return initial_factor_agent


def get_proof_check_agent(model_name="deepseek/deepseek-v3.2-exp"):
    from aether.agents import ProofCheckAgent

    client = get_client()

    proof_check_agent = ProofCheckAgent(
        model=model_name,
        client=client,
    )
    return proof_check_agent


def get_proof_fix_agent(model_name="deepseek/deepseek-v3.2-exp"):
    from aether.agents import ProofFixAgent

    client = get_client()

    proof_fix_agent = ProofFixAgent(
        model=model_name,
        client=client,
    )
    return proof_fix_agent


def get_factor_code_agent(model_name="deepseek/deepseek-v3.2-exp"):
    from aether.agents import FactorCodeAgent

    client = get_client()

    factor_code_agent = FactorCodeAgent(
        model=model_name,
        client=client,
    )
    return factor_code_agent


def get_nodes(provider: InMemoryDataProvider) -> list:
    from aether.clause import nodes

    P = 10

    NODES = [
        # 기본 수학 연산 노드들
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
        # 루트 노드들
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
        # 데이터 노드들 (label 파라미터 필요)
        nodes.DATA(label="OPEN", ticker="BTCUSDT", provider=provider),
        nodes.DATA(label="HIGH", ticker="BTCUSDT", provider=provider),
        nodes.DATA(label="LOW", ticker="BTCUSDT", provider=provider),
        nodes.DATA(label="CLOSE", ticker="BTCUSDT", provider=provider),
        nodes.DATA(label="VOLUME", ticker="BTCUSDT", provider=provider),
        nodes.DATA(label="PREMIUM_INDEX_CLOSE", ticker="BTCUSDT", provider=provider),
        nodes.DATA(label="FUNDING_RATE", ticker="BTCUSDT", provider=provider),
        nodes.DATA(label="RETURN", ticker="BTCUSDT", provider=provider),
        nodes.DATA(label="VWAP", ticker="BTCUSDT", provider=provider),
        nodes.DATA(label="VWAP", ticker="BTCUSDT", provider=provider),
        nodes.DATA(label="HOUR_SIN", ticker="BTCUSDT", provider=provider),
        nodes.DATA(label="HOUR_COS", ticker="BTCUSDT", provider=provider),
    ]

    return NODES
