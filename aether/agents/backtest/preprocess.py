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

    z = (arr - mu) / sig
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
    provider: InMemoryDataProvider, factor_func: Callable
) -> pd.DataFrame:
    factor_map = {}
    for ticker in provider.get_tickers():
        ticker_data = provider.get(ticker)
        ticker_series = factor_func(data=ticker_data)
        factor_map[ticker] = ticker_series
    return pd.DataFrame(factor_map)


def get_price_df(provider: InMemoryDataProvider) -> pd.DataFrame:
    price_map = {}
    for ticker in provider.get_tickers():
        ticker_data = provider.get(ticker)
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
