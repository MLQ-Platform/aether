from aether.clause import nodes
from aether.config import Config
from aether.config import get_config
from aether.provider import InMemoryDataProvider


def get_nodes(provider: InMemoryDataProvider, config: Config = None) -> list:
    config = config or get_config()
    P = config.clause.period
    START_DATE = config.data.start_date
    END_DATE = config.data.end_date
    TICKER = config.data.ticker
    DATA_KWARGS = {
        "ticker": TICKER,
        "provider": provider,
        "start_date": START_DATE,
        "end_date": END_DATE,
    }

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
            **DATA_KWARGS,
        ),
        nodes.DATA(
            label="HIGH",
            **DATA_KWARGS,
        ),
        nodes.DATA(
            label="LOW",
            **DATA_KWARGS,
        ),
        nodes.DATA(
            label="CLOSE",
            **DATA_KWARGS,
        ),
        nodes.DATA(
            label="VOLUME",
            **DATA_KWARGS,
        ),
        nodes.DATA(
            label="PREMIUM_INDEX_CLOSE",
            **DATA_KWARGS,
        ),
        nodes.DATA(
            label="PREMIUM_INDEX_OPEN",
            **DATA_KWARGS,
        ),
        nodes.DATA(
            label="PREMIUM_INDEX_HIGH",
            **DATA_KWARGS,
        ),
        nodes.DATA(
            label="PREMIUM_INDEX_LOW",
            **DATA_KWARGS,
        ),
        nodes.DATA(
            label="TAKER_BUY_VOLUME",
            **DATA_KWARGS,
        ),
        nodes.DATA(
            label="TAKER_SELL_VOLUME",
            **DATA_KWARGS,
        ),
        nodes.DATA(
            label="FUNDING_SCORE",
            **DATA_KWARGS,
        ),
        nodes.DATA(
            label="ORDER_FLOW_IMBALANCE",
            **DATA_KWARGS,
        ),
    ]

    return NODES
