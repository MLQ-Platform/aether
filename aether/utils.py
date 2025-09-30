import uuid
import pandas as pd


def generate_uuid() -> str:
    """
    Generate a unique UUID
    """
    return str(uuid.uuid4())[:8]


def clause_filter(
    series: pd.Series,
    min_count: int = 50,
    min_ratio: float = 0.20,
    max_ratio: float = 0.80,
) -> bool:
    """
    Clause Tree 결과 시계열(series)이 유효한지 여부를 판정.

    규칙:
      - True 발생 건수가 min_count 이상이어야 함.
      - True 발생 비율이 [min_ratio, max_ratio] 범위 안이어야 함.

    Args:
        series (pd.Series): bool 타입 시계열
        min_count (int): 최소 True 발생 횟수 (기본 50)
        min_ratio (float): 최소 True 발생 비율 컷 (기본 0.02 → 2%)
        max_ratio (float): 최대 True 발생 비율 컷 (기본 0.98 → 98%)

    Returns:
        bool: True면 사용 가능, False면 필터링 대상
    """
    if not isinstance(series, pd.Series):
        raise TypeError("series는 pd.Series여야 합니다.")
    if series.empty:
        return False
    if series.dtype != bool:
        raise ValueError("series는 bool dtype이어야 합니다.")

    T = len(series)
    count_true = int(series.sum())
    ratio = count_true / T

    if count_true < min_count:
        return False
    if ratio < min_ratio or ratio > max_ratio:
        return False

    return True
