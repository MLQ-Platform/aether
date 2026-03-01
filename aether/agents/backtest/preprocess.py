from typing import Callable
from typing import Optional
import numpy as np
import pandas as pd
from aether.agents.factor.schema import FactorCode
from aether.provider import InMemoryDataProvider


def code_to_callable(factor_code: FactorCode, context: dict = {}) -> Callable:
    FUNCTION_NAME = "factor"

    try:
        exec(factor_code.code, context)
        return context[FUNCTION_NAME]

    except Exception as e:
        raise ValueError(f"Failed to convert factor block to callable: {e}")


def resample_one_hour(df: pd.DataFrame) -> pd.DataFrame:
    return df.resample("1h").first()


def apply_zscore(factor_df: pd.DataFrame, min_obs: int = 6) -> pd.DataFrame:
    """
    Cross Sectional Z scoring
    """
    arr = factor_df.to_numpy(dtype=float)

    valid_cnt = np.sum(np.isfinite(arr), axis=1, keepdims=True)

    mu = np.full((arr.shape[0], 1), np.nan)
    sig = np.full((arr.shape[0], 1), np.nan)

    mask, _ = np.where(valid_cnt >= min_obs)
    mu[mask] = np.nanmean(arr[mask], axis=1, keepdims=True)
    sig[mask] = np.nanstd(arr[mask], axis=1, keepdims=True)

    z = (arr - mu) / (sig + 1e-10)
    z[~np.isfinite(arr)] = np.nan

    return pd.DataFrame(z, index=factor_df.index, columns=factor_df.columns)


def apply_winsorize(
    factor_df: pd.DataFrame, clip_sigma: float = 3.0, min_obs: int = 6
) -> pd.DataFrame:
    """
    Cross Sectional Winsorizing
    """
    arr = factor_df.to_numpy(dtype=float)  # (T, N)

    valid_cnt = np.sum(np.isfinite(arr), axis=1, keepdims=True)

    mu = np.full((arr.shape[0], 1), np.nan)
    sig = np.full((arr.shape[0], 1), np.nan)

    mask, _ = np.where(valid_cnt >= min_obs)
    mu[mask] = np.nanmean(arr[mask], axis=1, keepdims=True)
    sig[mask] = np.nanstd(arr[mask], axis=1, keepdims=True)

    upper = mu + clip_sigma * sig
    lower = mu - clip_sigma * sig

    clipped = np.clip(arr, lower, upper)
    clipped[~np.isfinite(arr)] = np.nan

    return pd.DataFrame(clipped, index=factor_df.index, columns=factor_df.columns)


def get_factor_df(
    provider: InMemoryDataProvider,
    factor_func: Callable,
    factor_params: dict,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    factor_map = {}
    for ticker in provider.get_tickers():
        ticker_data = provider.get(ticker).loc[start_date:end_date]
        ticker_series = factor_func(data=ticker_data, params=factor_params)
        factor_map[ticker] = ticker_series
    return pd.DataFrame(factor_map)


def get_price_df(
    provider: InMemoryDataProvider,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    price_map = {}
    for ticker in provider.get_tickers():
        ticker_data = provider.get(ticker).loc[start_date:end_date]
        price_map[ticker] = ticker_data["CLOSE"]
    return pd.DataFrame(price_map)


def get_alpha_df(
    factor_df: pd.DataFrame,
    price_df: pd.DataFrame,
    ic_series: Optional[pd.Series] = None,
    horizon: int = 6,
    window: int = 20,
) -> pd.DataFrame:
    """
    Grinold Alpha
    """

    if not ic_series:
        ic_series = get_ic_series(
            factor_df=factor_df, price_df=price_df, horizon=horizon
        )

    ret = price_df.pct_change(horizon, fill_method=None)
    vol_sma = ret.rolling(window).std()
    ic_sma = ic_series.rolling(window).mean()

    beta = vol_sma.values * ic_sma.values.reshape(-1, 1)
    alpha = beta * factor_df.values
    return pd.DataFrame(alpha, index=factor_df.index, columns=factor_df.columns)


def get_weight_df(alpha_df: pd.DataFrame, min_tickers: int = 6) -> pd.DataFrame:
    """
    Alpha to Neutralized Weight
    """
    alpha_arr = alpha_df.values

    valid_cnt = np.isfinite(alpha_arr).sum(axis=1)
    row_mask = valid_cnt > min_tickers

    mean = np.full((alpha_arr.shape[0], 1), np.nan)
    norm = np.full((alpha_arr.shape[0], 1), np.nan)

    mean[row_mask] = np.nanmean(alpha_arr[row_mask], axis=1, keepdims=True)
    norm[row_mask] = np.nansum(
        np.abs(alpha_arr[row_mask] - mean[row_mask]), axis=1, keepdims=True
    )

    weight = (alpha_arr - mean) / (norm + 1e-10)
    return pd.DataFrame(weight, index=alpha_df.index, columns=alpha_df.columns)


def get_ic_series(
    factor_df: pd.DataFrame,
    price_df: pd.DataFrame,
    horizon: int = 6,
    min_obs: int = 6,
) -> pd.Series:
    """
    Information Coefficient Series
    """

    # 1) forward-return
    px_arr = price_df.to_numpy(dtype=float)  # (T, N)
    fwd_px = np.roll(px_arr, -horizon, axis=0)  # P_{t+h}
    fwd_ret = (fwd_px - px_arr) / px_arr  # (P_{t+h}-P_t)/P_t
    fwd_ret[-horizon:, :] = np.nan

    # 2) Convert NumPy Array
    z_arr = factor_df.to_numpy(dtype=float)  # (T, N)
    ic_arr = np.full(z_arr.shape[0], np.nan, dtype=float)  # (T,)

    # 3) Row-wise Spearman
    for t, (z_row, r_row) in enumerate(zip(z_arr, fwd_ret)):
        mask = ~np.isnan(z_row) & ~np.isnan(r_row)
        n = mask.sum()

        # Cross Ticker Sample Minimum
        if n < min_obs:
            continue

        # (a) Ranking Vector
        z_rank = np.empty(n)
        r_rank = np.empty(n)
        z_rank[np.argsort(z_row[mask])] = np.arange(1, n + 1)
        r_rank[np.argsort(r_row[mask])] = np.arange(1, n + 1)

        # (b) Pearson Correlation
        cov = np.cov(z_rank, r_rank, ddof=0)
        ic_arr[t] = cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])

    return pd.Series(ic_arr, index=factor_df.index)


def apply_ewm(df: pd.DataFrame, alpha: float) -> pd.DataFrame:
    """
    Apply EMA per column, resetting state after each NaN gap.
    """

    if not 0 < alpha <= 1:
        raise ValueError("alpha must be in (0, 1]")

    arr = df.to_numpy(dtype=float, copy=True)
    n_rows, n_cols = arr.shape
    out = np.full((n_rows, n_cols), np.nan, dtype=float)

    for j in range(n_cols):
        x = arr[:, j]
        valid = np.isfinite(x)
        if not valid.any():
            continue

        y = np.empty(n_rows, dtype=float)
        prev = np.nan

        # O(T) single pass per column
        for i in range(n_rows):
            if not valid[i]:
                y[i] = np.nan
                prev = np.nan  # reset state on gap
                continue

            if np.isnan(prev):
                curr = x[i]  # restart EMA
            else:
                curr = alpha * x[i] + (1.0 - alpha) * prev

            y[i] = curr
            prev = curr

        out[:, j] = y

    return pd.DataFrame(out, index=df.index, columns=df.columns)


def apply_cap(weight_df: pd.DataFrame, min_cap: float, max_cap: float) -> pd.DataFrame:
    """
    Per-asset delta cap with deadband.

    Rules per timestamp t (vs previous executed weight):
    1) |delta| < min_cap  -> no trade on that asset (delta = 0)
    2) |delta| > max_cap  -> clip to sign(delta) * max_cap
    3) else               -> use original delta

    Then update executed weight:
        w_exec_t = w_exec_{t-1} + delta_capped

    Note:
    - min_cap, max_cap are in absolute weight units
    (e.g., 0.05 means 5%p weight change).
    - NaN target weights are treated as 0.0.
    """
    if min_cap < 0 or max_cap < 0:
        raise ValueError("min_cap and max_cap must be >= 0")
    if min_cap > max_cap:
        raise ValueError("min_cap must be <= max_cap")

    arr = weight_df.fillna(0.0).to_numpy(dtype=float)
    n_rows, n_cols = arr.shape

    out = np.zeros((n_rows, n_cols), dtype=float)
    prev = np.zeros(n_cols, dtype=float)

    for i in range(n_rows):
        delta = arr[i] - prev

        abs_delta = np.abs(delta)
        # below min_cap -> hold previous
        delta = np.where(abs_delta < min_cap, 0.0, delta)
        # above max_cap -> clip
        delta = np.clip(delta, -max_cap, max_cap)

        curr = prev + delta
        out[i] = curr
        prev = curr

    return pd.DataFrame(out, index=weight_df.index, columns=weight_df.columns)
