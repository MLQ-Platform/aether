from typing import Optional
import pandas as pd


class VectorizedBacktester:
    """
    Vectorized Backtester for Cross-Sectional Portfolio
    """

    # Initial Margin
    INITIAL_MARGIN = 1e2
    # Market Fee
    FEE = 0.05 / 100

    @classmethod
    def set_config(cls, initial_margin: float, fee: float):
        cls.INITIAL_MARGIN = initial_margin
        cls.FEE = fee

    @staticmethod
    def run(
        target_weight: pd.DataFrame,
        prices: pd.DataFrame,
        start_date: Optional[str] = "2021-01-01 00:00:00",
        end_date: Optional[str] = "2025-07-01 00:00:00",
    ) -> pd.Series:
        """
        Run the backtest

        Args:
            target_weight: pd.DataFrame with shape (n_steps, n_assets)
            prices: pd.DataFrame with shape (n_steps, n_assets)

        Returns:
            pd.Series with shape (n_steps,)
        """
        prices = prices.loc[start_date:end_date]
        weight = target_weight.loc[start_date:end_date]

        rets = prices.pct_change(fill_method=None).shift(-1) * weight
        ret = rets.sum(axis=1) - VectorizedBacktester.FEE

        cumulative_ret = 1 + ret.cumsum()
        portfolio_value = VectorizedBacktester.INITIAL_MARGIN * cumulative_ret
        return portfolio_value
