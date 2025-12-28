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

    def __init__(self, portfolio_value: pd.Series, freq: str = "1d"):
        """
        Args:
            portfolio_value: Portfolio value time series
            freq: Data frequency ('1min', '1h', '1d', '1w', '1m')
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
            "win_rate (%)": float(self._calculate_win_rate()),
            "pnl_rate": float(self._calculate_pnl_ratio()),
            "calmar_ratio": float(self._calculate_calmar_ratio()),
            "sortino_ratio": float(self._calculate_sortino_ratio()),
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

    def _calculate_calmar_ratio(self) -> float:
        """Calculate Calmar ratio"""

        annualized_return = self._calculate_annualized_expected_return()
        mdd = self._calculate_maximum_drawdown()

        if mdd == 0:
            return 0.0

        calmar_ratio = annualized_return / mdd
        return round(calmar_ratio, 4)

    def _calculate_sortino_ratio(self) -> float:
        """Calculate Sortino ratio"""

        annualized_return = self._calculate_annualized_expected_return()

        # Calculate downside returns only
        downside_returns = self._returns[self._returns < 0]

        if len(downside_returns) == 0:
            return 0.0

        downside_volatility = downside_returns.std() * np.sqrt(self._factor)

        if downside_volatility == 0:
            return 0.0

        sortino_ratio = annualized_return / downside_volatility
        return round(sortino_ratio, 4)
