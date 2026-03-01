from typing import Dict
import numpy as np
import pandas as pd


class Metric:
    """
    Cryptocurrency Strategy Performance Metric Calculator with Annualized Metrics
    """

    CRYPTO_ANNUALIZATION_FACTORS = {
        "1min": 60 * 24 * 365,
        "1h": 24 * 365,
        "1d": 365,
        "1w": 52,
        "1m": 12,
    }

    def __init__(
        self,
        portfolio_value: pd.Series,
        freq: str = "1d",
        fee: pd.Series | None = None,
        target_weight: pd.DataFrame | None = None,
    ):
        """
        Args:
            portfolio_value: Portfolio value time series
            freq: Data frequency ('1min', '1h', '1d', '1w', '1m')
            fee: Fee time series per period (optional)
            target_weight: Target weight dataframe for turnover calculation (optional)
        """

        if freq not in self.CRYPTO_ANNUALIZATION_FACTORS:
            raise ValueError(
                f"Unsupported frequency: {freq}. "
                f"Supported frequencies: {list(self.CRYPTO_ANNUALIZATION_FACTORS.keys())}"
            )

        if portfolio_value.empty:
            raise ValueError("Portfolio value is empty")

        self.portfolio_value = portfolio_value
        self._factor = self.CRYPTO_ANNUALIZATION_FACTORS[freq]
        self._returns = self._calculate_returns()
        self._fee = fee if fee is not None else pd.Series(dtype=float)
        self._turnover = self._prepare_turnover(target_weight=target_weight)

    def evaluate(self) -> Dict[str, float]:
        """
        Calculate and return all performance metrics
        """

        return {
            "annualized_expected_return (%)": float(
                self._calculate_annualized_expected_return()
            ),
            "annualized_volatility (%)": float(self._calculate_annualized_volatility()),
            "annualized_sharpe_ratio": float(self._calculate_annualized_sharpe_ratio()),
            "cumulative_return (%)": float(self._calculate_cumulative_return()),
            "maximum_drawdown (%)": float(self._calculate_maximum_drawdown()),
            "sharpe_ratio": float(self._calculate_sharpe_ratio()),
            "win_rate (%)": float(self._calculate_win_rate()),
            "pnl_rate": float(self._calculate_pnl_ratio()),
            "max_consecutive_wins": float(self._calculate_max_consecutive_wins()),
            "max_consecutive_losses": float(self._calculate_max_consecutive_losses()),
            "return_skewness": float(self._calculate_return_skewness()),
            "return_kurtosis": float(self._calculate_return_kurtosis()),
            "avg_daily_return (%)": float(self._calculate_avg_daily_return()),
            "total_fee": float(self._calculate_total_fee()),
            "avg_turnover": float(self._calculate_avg_turnover()),
        }

    def _calculate_returns(self) -> pd.Series:
        """Calculate returns"""
        return self.portfolio_value.pct_change().dropna()

    def _calculate_annualized_expected_return(self) -> float:
        """Calculate annualized expected return"""

        mean_return = self._returns.mean()
        annualized_return = mean_return * self._factor
        return round(annualized_return * 100, 4)

    def _calculate_annualized_volatility(self) -> float:
        """Calculate annualized volatility"""

        volatility = self._returns.std()
        annualized_volatility = volatility * np.sqrt(self._factor)
        return round(annualized_volatility * 100, 4)

    def _calculate_annualized_sharpe_ratio(self) -> float:
        """Calculate annualized Sharpe ratio"""

        annualized_return = self._calculate_annualized_expected_return()
        annualized_volatility = self._calculate_annualized_volatility()

        if annualized_volatility == 0:
            return 0.0

        sharpe_ratio = annualized_return / annualized_volatility
        return round(sharpe_ratio, 4)

    def _calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio"""

        mean_return = self._returns.mean()
        std_return = self._returns.std()

        return round(mean_return / (std_return + 1e-10), 4)

    def _calculate_maximum_drawdown(self) -> float:
        """Calculate maximum drawdown"""

        rolling_max = self.portfolio_value.expanding().max()
        drawdowns = (self.portfolio_value - rolling_max) / rolling_max
        mdd = drawdowns.min()
        return round(abs(mdd) * 100, 4)

    def _calculate_win_rate(self) -> float:
        """Calculate win rate"""

        winning_periods = (self._returns > 0).sum()
        total_periods = len(self._returns)
        win_rate = winning_periods / total_periods
        return round(win_rate * 100, 4)

    def _calculate_pnl_ratio(self) -> float:
        """Calculate profit/loss ratio"""

        diff = self.portfolio_value.diff()

        positive_returns = diff[diff > 0]
        negative_returns = diff[diff < 0]

        if len(positive_returns) == 0 or len(negative_returns) == 0:
            return 0.0

        avg_profit = positive_returns.sum()
        avg_loss = negative_returns.sum()

        if avg_loss == 0:
            return np.inf

        pl_ratio = abs(avg_profit / avg_loss)
        return round(pl_ratio, 4)

    def _calculate_cumulative_return(self) -> float:
        """Calculate total return"""

        cumulative_return = (
            self.portfolio_value.iloc[-1] / self.portfolio_value.iloc[0]
        ) - 1
        return round(cumulative_return * 100, 4)

    def _calculate_max_consecutive_by_mask(self, mask: pd.Series) -> int:
        """Calculate max consecutive True values from boolean mask"""

        if mask.empty:
            return 0

        groups = (~mask).cumsum()
        max_streak = mask.groupby(groups).sum()
        return int(max_streak.max()) if not max_streak.empty else 0

    def _calculate_max_consecutive_wins(self) -> int:
        """Calculate maximum consecutive wins"""

        return self._calculate_max_consecutive_by_mask(self._returns > 0)

    def _calculate_max_consecutive_losses(self) -> int:
        """Calculate maximum consecutive losses"""

        return self._calculate_max_consecutive_by_mask(self._returns < 0)

    def _calculate_return_skewness(self) -> float:
        """Calculate return skewness"""

        if self._returns.empty:
            return 0.0

        skewness = self._returns.skew()
        if np.isnan(skewness):
            return 0.0

        return round(float(skewness), 4)

    def _calculate_return_kurtosis(self) -> float:
        """Calculate return kurtosis (Fisher)"""

        if self._returns.empty:
            return 0.0

        kurtosis = self._returns.kurtosis()
        if np.isnan(kurtosis):
            return 0.0

        return round(float(kurtosis), 4)

    def _periods_per_day(self) -> float:
        """Get number of periods per day for current frequency"""

        return self._factor / 365

    def _calculate_avg_daily_return(self) -> float:
        """Calculate average daily return"""

        if self._returns.empty:
            return 0.0

        avg_daily_return = self._returns.mean() * self._periods_per_day()
        return round(avg_daily_return * 100, 4)

    def _calculate_total_fee(self) -> float:
        """Calculate total fee"""

        if self._fee.empty:
            return 0.0

        return round(float(self._fee.sum()), 4)

    def _calculate_avg_turnover(self) -> float:
        """Calculate average turnover per rebalance (notional=1.0)"""

        if self._turnover.empty:
            return 0.0

        return round(float(self._turnover.mean()), 4)

    def _prepare_turnover(self, target_weight: pd.DataFrame | None) -> pd.Series:
        """Prepare turnover series from target weight changes"""

        if target_weight is None or target_weight.empty:
            return pd.Series(dtype=float)

        # Turnover per rebalance: sum(abs(weight_t - weight_t-1))
        return target_weight.diff().abs().sum(axis=1, min_count=1).dropna()
