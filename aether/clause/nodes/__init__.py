from aether.clause.nodes.nodes import ABS
from aether.clause.nodes.nodes import ADD
from aether.clause.nodes.nodes import DATA
from aether.clause.nodes.nodes import DIFF
from aether.clause.nodes.nodes import DIV
from aether.clause.nodes.nodes import KURT
from aether.clause.nodes.nodes import MAX
from aether.clause.nodes.nodes import MIN
from aether.clause.nodes.nodes import SHIFT
from aether.clause.nodes.nodes import SKEW
from aether.clause.nodes.nodes import SMA
from aether.clause.nodes.nodes import STD
from aether.clause.nodes.nodes import SUB
from aether.clause.nodes.nodes import ZEXP
from aether.clause.nodes.nodes import ZSCORE
from aether.clause.nodes.nodes import Comparison
from aether.clause.nodes.nodes import CrossDown
from aether.clause.nodes.nodes import CrossUp
from aether.clause.nodes.nodes import DownStreak
from aether.clause.nodes.nodes import DrawdownExceed
from aether.clause.nodes.nodes import EqualApprox
from aether.clause.nodes.nodes import JumpDetect
from aether.clause.nodes.nodes import LargerThan
from aether.clause.nodes.nodes import MeanRevertKick
from aether.clause.nodes.nodes import NewHigh
from aether.clause.nodes.nodes import NewLow
from aether.clause.nodes.nodes import PctChange
from aether.clause.nodes.nodes import PullbackWithinBand
from aether.clause.nodes.nodes import ShiftSign
from aether.clause.nodes.nodes import SmallerThan
from aether.clause.nodes.nodes import UpStreak
from aether.clause.nodes.nodes import ZBetween
from aether.clause.nodes.nodes import ZSigmoid

__all__ = [
    "ABS",
    "ADD",
    "Comparison",
    "CORR",
    "DATA",
    "DIFF",
    "DIV",
    "NewHigh",
    "NewLow",
    "PctChange",
    "SHIFT",
    "ShiftSign",
    "SKEW",
    "SMA",
    "STD",
    "SUB",
    "ZSCORE",
    "KURT",
    "LargerThan",
    "SmallerThan",
    "ZBetween",
    "EqualApprox",
    "ZEXP",
    "ZSigmoid",
    "CrossUp",
    "CrossDown",
    "UpStreak",
    "DownStreak",
    "MeanRevertKick",
    "PullbackWithinBand",
    "DrawdownExceed",
    "JumpDetect",
    "MAX",
    "MIN",
]


from aether.provider import InMemoryDataProvider

provider = InMemoryDataProvider()

# 모든 노드들의 인스턴스를 포함한 리스트
NODES = [
    # 기본 수학 연산 노드들
    ADD(),
    DIV(),
    SUB(),
    ABS(),
    SMA(period=10),
    SHIFT(period=10),
    DIFF(period=10),
    PctChange(period=10),
    STD(period=10),
    NewHigh(period=10),
    NewLow(period=10),
    MAX(period=10),
    MIN(period=10),
    ZSCORE(period=10),
    SKEW(period=10),
    KURT(period=10),
    ZEXP(period=10),
    ZSigmoid(period=10),
    # 루트 노드들
    Comparison(),
    ZBetween(period=10, lo=-1.5, hi=1.5),
    EqualApprox(tol=1e-2),
    CrossUp(),
    CrossDown(),
    UpStreak(period=10),
    DownStreak(period=10),
    MeanRevertKick(period=10, z_th=1.0, dmax=10, eps=0.01),
    PullbackWithinBand(period=10, k=0.5),
    DrawdownExceed(pct=0.1, lookback=10),
    JumpDetect(period=10, q_tail=0.1),
    # 데이터 노드들 (label 파라미터 필요)
    DATA(label="OPEN", ticker="BTCUSDT", provider=provider),
    DATA(label="HIGH", ticker="BTCUSDT", provider=provider),
    DATA(label="LOW", ticker="BTCUSDT", provider=provider),
    DATA(label="CLOSE", ticker="BTCUSDT", provider=provider),
    DATA(label="VOLUME", ticker="BTCUSDT", provider=provider),
]
