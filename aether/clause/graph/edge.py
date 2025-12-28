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

        SU (Symmetrical Uncertainty) 의미:
        - SU는 두 변수 간의 정보 공유 정도를 정규화한 지표입니다.
        - 상호정보량(MI)을 두 변수의 엔트로피 합으로 정규화하여 [0, 1] 범위로 스케일링합니다.
        - 대칭적: SU(A,B) = SU(B,A)
        - 범위: [0, 1]
            * SU = 0: 두 변수가 독립적 (정보 공유 없음)
            * SU = 1: 두 변수가 완전히 의존적 (한 변수가 다른 변수를 완전히 결정)

        통계적 해석 가이드라인:
        - SU < 0.1: 약한 연관성 (weak association)
        - 0.1 ≤ SU < 0.3: 중간 연관성 (moderate association)
        - 0.3 ≤ SU < 0.5: 강한 연관성 (strong association)
        - SU ≥ 0.5: 매우 강한 연관성 (very strong association)

        주의사항:
        - SU는 효과 크기(effect size)를 나타내지만, 통계적 유의성은 별도로 검정해야 합니다.
        - 작은 샘플 크기에서는 높은 SU 값도 우연일 수 있으므로, 충분한 데이터 포인트(T)가 필요합니다.
        - alpha > 0을 사용하면 작은 샘플에서 더 안정적이지만, 약간의 편향을 도입할 수 있습니다.
        - 일반적으로 T ≥ 100 이상에서 해석하는 것이 권장됩니다.

        매개변수:
        series_a, series_b: bool dtype의 pd.Series. NaN은 공통 유효구간으로 마스킹.
        alpha: 라플라스 스무딩 파라미터(권장 0.5~1.0). 작은 샘플에서 안정성을 높입니다.
        detail: True이면 SU 외에 H_A, H_B, H_AB, MI, T, counts, p_table을 포함한 dict 반환.
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
