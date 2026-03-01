from __future__ import annotations
import traceback
import warnings
from pathlib import Path
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from aether import factory
from aether.agents.backtest import Metric
from aether.agents.backtest import VectorizedBacktester
from aether.agents.backtest.preprocess import apply_cap
from aether.agents.backtest.preprocess import apply_ewm
from aether.agents.backtest.preprocess import code_to_callable
from aether.agents.backtest.preprocess import get_alpha_df
from aether.agents.backtest.preprocess import get_factor_df
from aether.agents.backtest.preprocess import get_price_df
from aether.agents.backtest.preprocess import get_weight_df
from aether.agents.backtest.preprocess import resample_one_hour
from aether.agents.factor.schema import FactorCode
from aether.config import get_config
from aether.logger import get_logger
from aether.utils import load_json
from aether.utils import save_json

logger = get_logger(__name__)


def _build_weight_df(provider, factor_code_path: Path, bt_cfg):
    factor_data = load_json(str(factor_code_path))
    factor_code = FactorCode(code=factor_data["code"])
    factor_func = code_to_callable(factor_code)
    factor_params = factor_data.get("params", {})

    factor_df = get_factor_df(
        provider=provider,
        factor_func=factor_func,
        factor_params=factor_params,
        start_date=bt_cfg.start_date,
        end_date=bt_cfg.end_date,
    )
    price_df = get_price_df(
        provider=provider,
        start_date=bt_cfg.start_date,
        end_date=bt_cfg.end_date,
    )

    alpha_df = get_alpha_df(
        factor_df=factor_df,
        price_df=price_df,
        horizon=bt_cfg.alpha_horizon,
        window=bt_cfg.alpha_window,
    )

    alpha_df = apply_ewm(
        df=alpha_df,
        alpha=bt_cfg.ewm_alpha,
    )

    weight_df = get_weight_df(
        alpha_df=alpha_df,
        min_tickers=bt_cfg.min_tickers,
    )

    weight_df = apply_cap(
        weight_df=weight_df,
        min_cap=bt_cfg.min_cap,
        max_cap=bt_cfg.max_cap,
    )

    weight_df = resample_one_hour(df=weight_df)
    price_df = resample_one_hour(df=price_df)
    return weight_df, price_df


def _run_backtest(weight_df, price_df, bt_cfg):
    tester = VectorizedBacktester()
    tester.set_config(initial_margin=bt_cfg.initial_margin, fee=bt_cfg.fee)

    portfolio_value = tester.run(
        target_weight=weight_df,
        prices=price_df,
        start_date=bt_cfg.start_date,
        end_date=bt_cfg.end_date,
    )
    metric = Metric(
        portfolio_value=portfolio_value,
        freq="1h",
        target_weight=weight_df,
    ).evaluate()
    return portfolio_value, metric


def _save_pv_plot(portfolio_value, save_path: Path) -> None:
    plt.figure(figsize=(20, 4))
    plt.plot(portfolio_value.index, portfolio_value.values, linewidth=1.2)
    plt.title("Portfolio Value")
    plt.xlabel("Datetime")
    plt.ylabel("Value")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()


def _configure_warning_filters() -> None:
    warnings.simplefilter("ignore")


def run_batch_factor_backtests(
    factor_dir: str | Path = "database/factor",
    backtest_dir: str | Path = "database/backtest",
) -> dict:
    config = get_config()
    bt_cfg = config.backtest
    provider = factory.get_provider()

    factor_dir = Path(factor_dir)
    backtest_dir = Path(backtest_dir)
    backtest_dir.mkdir(parents=True, exist_ok=True)

    factor_files = sorted(factor_dir.glob("*.json"))
    summary = {
        "total": len(factor_files),
        "processed": 0,
        "skipped_existing": 0,
        "failed": 0,
        "outputs": [],
    }

    _configure_warning_filters()
    logger.info(f"Backtest start total={summary['total']}")

    for factor_path in factor_files:
        factor_id = factor_path.stem
        out_dir = backtest_dir / factor_id

        if out_dir.exists():
            summary["skipped_existing"] += 1
            logger.info(f"Skip {factor_id}")
            continue

        out_dir.mkdir(parents=True, exist_ok=False)

        try:
            logger.info(f"Run {factor_id}")

            with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    weight_df, price_df = _build_weight_df(
                        provider, factor_path, bt_cfg
                    )
                    portfolio_value, metric = _run_backtest(weight_df, price_df, bt_cfg)

            metric_path = out_dir / "metric.json"
            plot_path = out_dir / "pv.png"

            save_json(metric, str(metric_path))
            _save_pv_plot(portfolio_value, plot_path)

            summary["processed"] += 1
            summary["outputs"].append(
                {
                    "factor": factor_id,
                    "metric": str(metric_path),
                    "plot": str(plot_path),
                }
            )
            logger.info(f"Done {factor_id}")

        except Exception as e:
            summary["failed"] += 1
            error_metric = {
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
            save_json(error_metric, str(out_dir / "metric.json"))
            logger.warning(f"Failed: {factor_id} ({e})")

    logger.info(
        f"Backtest done p={summary['processed']} s={summary['skipped_existing']} f={summary['failed']}"
    )
    return summary
