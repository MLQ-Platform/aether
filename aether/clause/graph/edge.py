from collections import Counter
from typing import Any
from typing import Callable
from typing import List
import numpy as np
import pandas as pd
from aether.clause.tree.base import ClauseTree
from aether.logger import get_logger

logger = get_logger(__name__)


class EdgeCalculator:
    """
    Edge Calculator Base Class
    """

    @staticmethod
    def calculate(
        series_a: pd.Series,
        series_b: pd.Series,
    ) -> float:
        """
        Calculate edge weight between two series
        """
        raise NotImplementedError("Subclass must implement this method")


class SUEdgeCalculator(EdgeCalculator):
    """
    Symmetric Uncertainty Edge Calculator
    """

    @staticmethod
    def calculate(
        series_a: pd.Series,
        series_b: pd.Series,
        alpha: float = 0.0,
        detail: bool = False,
    ) -> float:
        """
        Boolean 시계열 a, b에 대해 상호정보량(MI)과 Symmetrical Uncertainty(SU)를 계산

        정의:
        - 2x2 분할표 카운트: n11, n10, n01, n00
        - 라플라스 스무딩(조인트 분포는 K=4 상태):
            p_ij = (n_ij + alpha) / (T + 4*alpha)
        - 주변확률:
            pA1 = p11 + p10,  pA0 = p01 + p00
            pB1 = p11 + p01,  pB0 = p10 + p00
        - 엔트로피:
            H(A)   = -Σ_x pA(x) log pA(x)
            H(B)   = -Σ_y pB(y) log pB(y)
            H(A,B) = -Σ_{x,y} p(x,y) log p(x,y)
        - 상호정보량: I(A;B) = H(A) + H(B) - H(A,B)
        - 대칭 불확실성: SU = 2*I / (H(A)+H(B))   (분모가 0이면 SU=0)

        매개변수:
        a, b     : bool dtype의 pd.Series. NaN은 공통 유효구간으로 마스킹.
        alpha    : 라플라스 스무딩 파라미터(권장 0.5~1.0).
        log_base : 로그 밑 (기본값 e). 2 또는 10 등으로 변경 가능.
        """

        if not isinstance(series_a, pd.Series) or not isinstance(series_b, pd.Series):
            raise TypeError("a, b는 pd.Series 여야 합니다.")

        # 공통 유효 구간만 사용
        mask = series_a.notna() & series_b.notna()
        series_a = series_a[mask].astype(bool)
        series_b = series_b[mask].astype(bool)
        T = int(series_a.size)

        if T == 0:
            raise Exception("No valid data points")

        # 2x2 분할표 카운트
        n11 = int((series_a & series_b).sum())
        n10 = int((series_a & ~series_b).sum())
        n01 = int((~series_a & series_b).sum())
        n00 = int((~series_a & ~series_b).sum())

        # 라플라스 스무딩 (joint: K=4 상태)
        denom = T + 4.0 * alpha
        p11 = (n11 + alpha) / denom
        p10 = (n10 + alpha) / denom
        p01 = (n01 + alpha) / denom
        p00 = (n00 + alpha) / denom

        # 주변확률(조인트에서 유도)
        pA1, pA0 = (p11 + p10), (p01 + p00)
        pB1, pB0 = (p11 + p01), (p10 + p00)

        # 안전한 엔트로피 계산
        def H_from_probs(ps: np.ndarray) -> float:
            # ps: 확률 벡터, 합=1 가정. 0*log(0)=0 처리.
            ps = np.asarray(ps, dtype=float)
            ps = ps[(ps > 0)]  # 0은 항에서 제외

            if ps.size == 0:
                return 0.0
            return float(-np.sum(ps * np.log(ps)))

        H_A = H_from_probs(np.array([pA1, pA0]))
        H_B = H_from_probs(np.array([pB1, pB0]))
        H_AB = H_from_probs(np.array([p11, p10, p01, p00]))
        MI = H_A + H_B - H_AB

        denom_su = H_A + H_B
        SU = 0.0 if denom_su <= 0.0 else float(2.0 * MI / denom_su)

        if not detail:
            return SU

        return {
            "H_A": H_A,
            "H_B": H_B,
            "H_AB": H_AB,
            "MI": float(MI),
            "SU": SU,
            "T": T,
            "counts": (n11, n10, n01, n00),
            "p_table": {(1, 1): p11, (1, 0): p10, (0, 1): p01, (0, 0): p00},
        }
