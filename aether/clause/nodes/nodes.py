from math import erf
from math import sqrt
import numpy as np
import pandas as pd
from aether.clause.nodes.base import Node
from aether.clause.nodes.base import NodeIOTypes
from aether.provider import InMemoryDataProvider


class DATA(Node):
    """
    Data 값을 담은 리프 노드 (ex: 시장 데이터)
    """

    def __init__(self, label, ticker):
        super(DATA, self).__init__(
            input_types=[],
            output_type=NodeIOTypes.FLOAT,
            max_childs=0,
        )
        self.label = label
        self.ticker = ticker
        self.provider = InMemoryDataProvider()

    @property
    def name(self):
        return type(self).__name__ + f"[{self.label}]"

    def activate(self):
        if not self.provider.has(self.ticker):
            raise ValueError(f"No Data for {self.ticker}")

        return self.provider.get(self.ticker)[self.label]


class SMA(Node):
    """
    Simple Moving Average 연산 노드
    """

    def __init__(self, period):
        super(SMA, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.FLOAT,
            max_childs=1,
        )
        self.period = period

    @property
    def name(self):
        return type(self).__name__ + f"({self.period})"

    def activate(self, seq):
        return seq.rolling(self.period).mean()


class ADD(Node):
    """
    두 개의 value를 더하는 연산 노드
    """

    def __init__(self):
        super(ADD, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.FLOAT,
            max_childs=2,
        )

    def activate(self, a, b):
        return a + b


class SHIFT(Node):
    """
    Seqence data shift를 period 만큼 shift 연산 노드
    """

    def __init__(self, period):
        super(SHIFT, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.FLOAT,
            max_childs=1,
        )
        self.period = period

    @property
    def name(self):
        return type(self).__name__ + f"({self.period})"

    def activate(self, seq):
        return seq.shift(self.period)


class DIFF(Node):
    """
    (n)번째 행과 (n-peirod)번째 행과의 차이 연산 노드
    """

    def __init__(self, period):
        super(DIFF, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.FLOAT,
            max_childs=1,
        )
        self.period = period

    @property
    def name(self):
        return type(self).__name__ + f"({self.period})"

    def activate(self, seq):
        return seq.diff(self.period)


class PctChange(Node):
    """
    (n)번째 행과 (n-peirod)번째 행과의 변화율 연산 노드
    """

    def __init__(self, period):
        super(PctChange, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.FLOAT,
            max_childs=1,
        )
        self.period = period

    @property
    def name(self):
        return type(self).__name__ + f"({self.period})"

    def activate(self, seq):
        return seq.pct_change(self.period, fill_method=None).ffill()


class ShiftSign(Node):
    """
    부호 shift 연산 노드
    """

    def __init__(self):
        super(ShiftSign, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.FLOAT,
            max_childs=1,
        )

    def activate(self, seq):
        return -seq


class ABS(Node):
    """
    절댓값 연산 노드
    """

    def __init__(self):
        super(ABS, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.FLOAT,
            max_childs=1,
        )

    def activate(self, seq):
        return np.abs(seq)


class DIV(Node):
    """
    두 값의 나눗셈 연산 노드
    """

    def __init__(self):
        super(DIV, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.FLOAT,
            max_childs=2,
        )

    def activate(self, a, b):
        return a / (b + 1e-10)


class SUB(Node):
    """
    두 값의 a-b 계산 노드
    """

    def __init__(self):
        super(SUB, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.FLOAT,
            max_childs=2,
        )

    def activate(self, a, b):
        return a - b


class Comparison(Node):
    """
    두 값 a, b에 대하여 a > b 여부 연산 노드
    """

    def __init__(self):
        super(Comparison, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.BINARY,
            max_childs=2,
        )

    def activate(self, a, b):
        return a > b


class NewHigh(Node):
    """
    New High 갱신 여부 연산 노드
    """

    def __init__(self, period):
        super(NewHigh, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.BINARY,
            max_childs=1,
        )
        self.period = period

    @property
    def name(self):
        return type(self).__name__ + f"({self.period})"

    def activate(self, seq):
        return seq.rolling(self.period).max() == seq


class NewLow(Node):
    """
    New Low 갱신 여부 연산 노드
    """

    def __init__(self, period):
        super(NewLow, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.BINARY,
            max_childs=1,
        )
        self.period = period

    @property
    def name(self):
        return type(self).__name__ + f"({self.period})"

    def activate(self, seq):
        return seq.rolling(self.period).min() == seq


class ZSCORE(Node):
    """
    롤링 윈도우로 Z-score 계산 노드
    """

    def __init__(self, period):
        super(ZSCORE, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.FLOAT,
            max_childs=1,
        )
        self.period = period

    @property
    def name(self):
        return type(self).__name__ + f"({self.period})"

    def activate(self, seq: pd.Series):
        rolling_mean = seq.rolling(self.period).mean()
        rolling_std = seq.rolling(self.period).std()
        zscore = (seq - rolling_mean) / rolling_std
        return zscore


class STD(Node):
    """
    롤링 표준편차 연산 노드
    """

    def __init__(self, period):
        super(STD, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.FLOAT,
            max_childs=1,
        )
        self.period = period

    @property
    def name(self):
        return type(self).__name__ + f"({self.period})"

    def activate(self, seq):
        return seq.rolling(self.period).std()


class MAX(Node):
    """
    롤링 최댓값 연산 노드
    """

    def __init__(self, period):
        super(MAX, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.FLOAT,
            max_childs=1,
        )

        self.period = period

    @property
    def name(self):
        return type(self).__name__ + f"({self.period})"

    def activate(self, seq):
        return seq.rolling(self.period).max()


class MIN(Node):
    """
    롤링 최솟값 연산 노드
    """

    def __init__(self, period):
        super(MIN, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.FLOAT,
            max_childs=1,
        )

        self.period = period

    @property
    def name(self):
        return type(self).__name__ + f"({self.period})"

    def activate(self, seq):
        return seq.rolling(self.period).min()


class SKEW(Node):
    """
    왜도 (Skewness) 계산 노드
    """

    def __init__(self, period):
        super(SKEW, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.FLOAT,
            max_childs=1,
        )
        self.period = period

    @property
    def name(self):
        return type(self).__name__ + f"({self.period})"

    def activate(self, seq):
        return seq.rolling(self.period).skew()


class KURT(Node):
    """
    첨도 (Kurtosis) 계산 노드
    """

    def __init__(self, period):
        super(KURT, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.FLOAT,
            max_childs=1,
        )
        self.period = period

    @property
    def name(self):
        return type(self).__name__ + f"({self.period})"

    def activate(self, seq):
        return seq.rolling(self.period).kurt()


class LargerThan(Node):
    """
    주어진 값 (n) 보다 큰지 여부 연산 노드
    """

    def __init__(self, n):
        super(LargerThan, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.BINARY,
            max_childs=1,
        )
        self.n = n

    @property
    def name(self):
        return type(self).__name__ + f"({self.n})"

    def activate(self, seq):
        return seq > self.n


class SmallerThan(Node):
    """
    주어진 값 (n) 보다 작은지 여부 연산 노드
    """

    def __init__(self, n):
        super(SmallerThan, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.BINARY,
            max_childs=1,
        )
        self.n = n

    def activate(self, seq):
        return seq < self.n


class ZBetween(Node):
    """
    주어진 시계열의 zscore가 범위 내에 있는지 여부 연산 노드
    """

    def __init__(self, period, lo, hi):
        super(ZBetween, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.BINARY,
            max_childs=1,
        )
        self.period = period
        self.lo = lo
        self.hi = hi

    @property
    def name(self):
        return (
            type(self).__name__
            + f"({self.period}, {round(self.lo, 4)}, {round(self.hi, 4)})"
        )

    def activate(self, seq):
        rolling_mean = seq.rolling(self.period).mean()
        rolling_std = seq.rolling(self.period).std()
        zscore = (seq - rolling_mean) / (rolling_std + 1e-5)
        return (zscore >= self.lo) & (zscore <= self.hi)


class EqualApprox(Node):
    """
    두 시계열 값이 근사한지 여부 연산 노드
    """

    def __init__(self, tol=1e-2):
        super(EqualApprox, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.BINARY,
            max_childs=2,
        )
        self.tol = tol

    @property
    def name(self):
        return type(self).__name__ + f"({round(self.tol, 4)})"

    def activate(self, a, b):
        return (a - b).abs() <= self.tol


class ZEXP(Node):
    """
    Z-score 정규화 후 Exp 연산 노드
    """

    def __init__(self, period):
        super(ZEXP, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.FLOAT,
            max_childs=1,
        )
        self.period = period

    @property
    def name(self):
        return type(self).__name__ + f"({self.period})"

    def activate(self, seq):
        rolling_mean = seq.rolling(self.period).mean()
        rolling_std = seq.rolling(self.period).std()
        zscore = (seq - rolling_mean) / (rolling_std + 1e-5)
        return np.exp(zscore)


class ZSigmoid(Node):
    """
    Sigmoid 연산 노드
    """

    def __init__(self, period):
        super(ZSigmoid, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.FLOAT,
            max_childs=1,
        )

        self.period = period

    @property
    def name(self):
        return type(self).__name__ + f"({self.period})"

    def activate(self, seq):
        rolling_mean = seq.rolling(self.period).mean()
        rolling_std = seq.rolling(self.period).std()
        zscore = (seq - rolling_mean) / (rolling_std + 1e-5)
        return 1.0 / (1.0 + np.exp(-zscore))


class CrossUp(Node):
    """
    Cross Up 연산 노드
    """

    def __init__(self):
        super(CrossUp, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.BINARY,
            max_childs=2,
        )

    def activate(self, seq, seq2):
        return (seq > seq2) & (seq.shift(1) <= seq2.shift(1))


class CrossDown(Node):
    """
    Cross Down 연산 노드
    """

    def __init__(self):
        super(CrossDown, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.BINARY,
            max_childs=2,
        )

    def activate(self, seq, seq2):
        return (seq < seq2) & (seq.shift(1) >= seq2.shift(1))


class SlopeSignChange(Node):
    """
    최근 window 구간의 선형회귀 기울기 부호가 직전 대비 전환되는 순간을 포착
    """

    def __init__(self, p: int):
        super(SlopeSignChange, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.BINARY,
            max_childs=1,
        )
        self.p = p

    @property
    def name(self):
        return type(self).__name__ + f"({self.p})"

    @staticmethod
    def _rolling_slope(x: np.ndarray) -> float:
        # x: 1D ndarray (길이 window), NaN 포함 가능
        idx = np.arange(x.size)
        mask = ~np.isnan(x)

        if mask.sum() < 2:
            return np.nan

        xv = idx[mask]
        yv = x[mask]
        # 1차 선형회귀 slope
        slope = np.polyfit(xv, yv, 1)[0]
        return slope

    def activate(self, seq: pd.Series) -> pd.Series:
        slope = seq.rolling(self.p, min_periods=self.p).apply(
            self._rolling_slope, raw=True
        )
        sign = np.sign(slope)
        out = (sign != sign.shift(1)) & sign.notna() & sign.shift(1).notna()
        return out.fillna(False)


class UpStreak(Node):
    """
    시계열이 연속 k기간 증가(Δ>0)한 시점에 트리거
    """

    def __init__(self, p: int):
        super(UpStreak, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.BINARY,
            max_childs=1,
        )
        self.p = p

    @property
    def name(self):
        return type(self).__name__ + f"({self.p})"

    def activate(self, seq: pd.Series) -> pd.Series:
        inc = (seq.diff() > 0).astype(int)

        # 런 길이 계산: 동일 상태 구간별 카운트 누적
        grp = (inc != inc.shift()).cumsum()
        runlen = inc.groupby(grp).cumsum()

        out = runlen >= self.p
        return out.fillna(False)


class DownStreak(Node):
    """
    시계열이 연속 k기간 감소(Δ<0)한 시점에 트리거
    """

    def __init__(self, p: int):
        super(DownStreak, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.BINARY,
            max_childs=1,
        )
        self.p = p

    @property
    def name(self):
        return type(self).__name__ + f"({self.p})"

    def activate(self, seq: pd.Series) -> pd.Series:
        dec = (seq.diff() < 0).astype(int)

        grp = (dec != dec.shift()).cumsum()
        runlen = dec.groupby(grp).cumsum()

        out = runlen >= self.p
        return out.fillna(False)


class MeanRevertKick(Node):
    """
    극단(z-score) 상태 진입 후 Dmax 이내에 중심(평균) 방향으로 유의미하게 되돌아오는 포인트 캐치
    """

    def __init__(
        self,
        p: int,
        z_th: float,
        dmax: int,
        eps: float,
    ):
        super(MeanRevertKick, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.BINARY,
            max_childs=1,
        )
        assert p >= 2

        self.p = p
        self.z_th = z_th
        self.dmax = dmax
        self.eps = eps

    @property
    def name(self):
        return (
            type(self).__name__
            + f"(p={self.p}, z_th={round(self.z_th, 3)}, dmax={self.dmax})"
        )

    def activate(self, seq: pd.Series) -> pd.Series:
        """
        1. z_window로 z-score 계산
        2. |z_t| >= z_th 진입점 이후,
        3. 향후 Dmax 내에서 |z|가 (|z_t|-eps) 미만으로 감소하면 트리거.
        """

        mu = seq.rolling(self.p, min_periods=self.p).mean()
        sd = seq.rolling(self.p, min_periods=self.p).std()
        z = (seq - mu) / (sd + 1e-5)
        abs_z = z.abs()

        enter = abs_z >= self.z_th

        # 향후 Dmax 내 최소 |z| 계산 (자기 시점 이후 타임 스텝부터 체크)
        future_min_abs_z = (
            abs_z[::-1].rolling(self.dmax + 1, min_periods=1).min()[::-1].shift(-1)
        )

        kick = future_min_abs_z < (abs_z - self.eps)
        out = enter & kick
        return out.fillna(False)


class PullbackWithinBand(Node):
    """
    밴드 안쪽으로 재진입하는 포인트 캐치
    """

    def __init__(self, p: int, k: float):
        super(PullbackWithinBand, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.BINARY,
            max_childs=1,
        )
        self.p = p
        self.k = float(k)

    @property
    def name(self):
        return type(self).__name__ + f"({self.p}, k={round(self.k, 3)})"

    def activate(self, seq: pd.Series) -> pd.Series:
        mu = seq.rolling(self.p, min_periods=self.p).mean()
        sd = seq.rolling(self.p, min_periods=self.p).std()
        upper = mu + self.k * sd
        lower = mu - self.k * sd

        # 상단→내부, 하단→내부 재진입
        reenter_from_top = (seq.shift(1) > upper.shift(1)) & (seq <= upper)
        reenter_from_bot = (seq.shift(1) < lower.shift(1)) & (seq >= lower)

        out = reenter_from_top | reenter_from_bot
        return out.fillna(False)


class DrawdownExceed(Node):
    """
    최근 lookback 고점 대비 드로다운이 pct 이상으로 확대되는 포인트 캐치
    """

    def __init__(self, pct: float, lookback: int):
        super(DrawdownExceed, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.BINARY,
            max_childs=1,
        )
        assert 0.0 < pct < 1.0

        self.pct = pct
        self.lookback = lookback

    @property
    def name(self):
        return type(self).__name__ + f"(pct={round(self.pct, 3)}, lb={self.lookback})"

    def activate(self, seq: pd.Series) -> pd.Series:
        roll_max = seq.rolling(self.lookback, min_periods=self.lookback).max()
        dd = 1.0 - (seq / roll_max)
        out = dd >= self.pct
        return out.fillna(False)


class JumpDetect(Node):
    """
    의도: 변화량(|Δ|)이 최근 window 분포의 상위 (1 - q_tail) 분위 이상(꼬리 q_tail)인 '점프'를 포착한다.
    - 예: q_tail=0.10이면 상위 10% 절대변화 이상을 이벤트로 본다.
    """

    def __init__(self, p: int, q_tail: float):
        super(JumpDetect, self).__init__(
            input_types=[NodeIOTypes.FLOAT],
            output_type=NodeIOTypes.BINARY,
            max_childs=1,
        )
        assert 0.0 < q_tail < 1.0
        self.p = p
        self.q_tail = q_tail

    @property
    def name(self):
        return type(self).__name__ + f"(p={self.p}, tail={round(self.q_tail, 3)})"

    def activate(self, seq: pd.Series) -> pd.Series:
        r = seq.diff().abs()
        thresh = r.rolling(self.p, min_periods=self.p).quantile(1.0 - self.q_tail)
        out = r >= thresh
        return out.fillna(False)
