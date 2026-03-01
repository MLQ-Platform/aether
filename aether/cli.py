import asyncio
import os
import time
from dataclasses import asdict
import typer
from aether.display import show_closer
from aether.display import show_cli_banner
from aether.display import show_config_display
from aether.display import show_error_block
from aether.display import show_header
from aether.display import show_run_plan
from aether.display import show_step_result
from aether.display import show_summary
from aether.display import step_progress

app = typer.Typer(
    name="aether",
    help="AETHER - Data-driven Hypothesis Generation Engine",
    add_completion=False,
    invoke_without_command=True,
)

_verbose = False
_skip_confirm = False


def _version_callback(value: bool):
    if value:
        from aether import __version__

        typer.echo(f"aether {__version__}")
        raise typer.Exit()


@app.callback()
def callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
):
    """AETHER - Data-driven Hypothesis Generation Engine"""
    if ctx.invoked_subcommand is None and not version:
        show_cli_banner()
        typer.echo(ctx.get_help())
        raise typer.Exit(code=0)

    global _verbose, _skip_confirm
    _verbose = verbose
    _skip_confirm = yes
    from aether.logger import init_cli

    init_cli(verbose)


def _run_async(coro):
    """Run an async coroutine, closing AsyncOpenAI clients before the loop closes."""

    async def _wrapper():
        try:
            return await coro
        finally:
            from aether.factory import cleanup_async_clients

            await cleanup_async_clients()

    return asyncio.run(_wrapper())


def _pluralize(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular if count == 1 else plural}"


def _time_summary(total_time: float, iter_count: int) -> str:
    if iter_count > 1:
        return f"{total_time:.1f}s ({total_time / iter_count:.1f}s/iter)"
    return f"{total_time:.1f}s"


@app.command()
def clause(
    version: str = typer.Option("v0", "--version", help="Clause graph version tag"),
    output_dir: str | None = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
    config_path: str | None = typer.Option(
        None, "--config", "-c", help="Config YAML path"
    ),
):
    """Generate a ClauseGraph from random indicator trees."""
    try:
        from aether.config import get_config
        from aether.config import resolve_path
        from aether.pipeline.clause import build_clause_graph

        config = get_config(config_path)
        show_header(model=config.llm.model, ticker=config.data.ticker)
        save_dir = output_dir or os.path.join(
            resolve_path(config.data.database_dir), "clause"
        )

        if not show_run_plan(
            "Clause Generation",
            config=config,
            output_path=save_dir,
            skip_confirm=_skip_confirm,
        ):
            show_closer("Cancelled")
            raise typer.Exit(code=0)

        total_start = time.time()
        with step_progress("Building Clause Graph") as ctx:
            clause_graph = build_clause_graph(
                config, on_progress=lambda e, i: ctx.update(f"{e} edges")
            )
            ctx.detail(
                f"{clause_graph.num_nodes} nodes, {clause_graph.num_edges} edges"
            )
        show_step_result(
            f"{clause_graph.num_nodes} nodes, {clause_graph.num_edges} edges"
        )

        os.makedirs(save_dir, exist_ok=True)
        clause_graph.save(os.path.join(save_dir, f"clause-{version}.json"))

        total_time = time.time() - total_start
        show_summary(
            [
                ("Total", "1 clause graph"),
                ("Time", f"{total_time:.1f}s"),
                ("Output", save_dir),
            ]
        )
        show_closer(elapsed=total_time)
    except typer.Exit:
        raise
    except Exception as e:
        show_error_block("Clause Generation Failed", str(e), verbose=_verbose)
        raise typer.Exit(code=1)


@app.command()
def thesis(
    clause_version: str = typer.Option(
        "v0", "--clause-version", help="Clause graph version to load"
    ),
    clause_dir: str | None = typer.Option(
        None, "--clause-dir", help="Clause graph directory"
    ),
    output_dir: str | None = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
    config_path: str | None = typer.Option(
        None, "--config", "-c", help="Config YAML path"
    ),
    parallel: int = typer.Option(1, "--parallel", "-p", help="Number of parallel runs"),
    iter_count: int = typer.Option(1, "--iter", "-n", help="Number of iterations"),
):
    """Generate a thesis from a ClauseGraph subgraph."""
    try:
        from aether.config import get_config
        from aether.config import resolve_path
        from aether.pipeline.runner import run_thesis
        from aether.pipeline.runner import run_thesis_parallel

        config = get_config(config_path)
        show_header(model=config.llm.model, ticker=config.data.ticker)
        output_path = output_dir or os.path.join(
            resolve_path(config.data.database_dir), "thesis"
        )

        if not show_run_plan(
            "Thesis Generation",
            parallel,
            iter_count,
            config=config,
            output_path=output_path,
            skip_confirm=_skip_confirm,
        ):
            show_closer("Cancelled")
            raise typer.Exit(code=0)

        total_count = 0
        total_start = time.time()

        for i in range(iter_count):
            iter_label = f"Iter {i + 1}/{iter_count}" if iter_count > 1 else None
            if parallel > 1:
                with step_progress(
                    f"Generating {parallel} Theses (parallel)", iter_label=iter_label
                ):
                    result = _run_async(
                        run_thesis_parallel(
                            clause_load_basedir=clause_dir,
                            thesis_save_basedir=output_dir,
                            clause_version=clause_version,
                            num_parallel=parallel,
                        )
                    )
                count = len(result)
            else:
                with step_progress("Generating Thesis", iter_label=iter_label):
                    run_thesis(
                        clause_load_basedir=clause_dir,
                        thesis_save_basedir=output_dir,
                        clause_version=clause_version,
                    )
                count = 1
            total_count += count
            show_step_result(_pluralize(count, "thesis", "theses") + " generated")

        total_time = time.time() - total_start
        show_summary(
            [
                ("Total", _pluralize(total_count, "thesis", "theses")),
                ("Time", _time_summary(total_time, iter_count)),
                ("Output", output_path),
            ]
        )
        show_closer(elapsed=total_time)
    except typer.Exit:
        raise
    except Exception as e:
        show_error_block("Thesis Generation Failed", str(e), verbose=_verbose)
        raise typer.Exit(code=1)


@app.command()
def claim(
    thesis_dir: str | None = typer.Option(
        None, "--thesis-dir", help="Thesis directory"
    ),
    output_dir: str | None = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
    config_path: str | None = typer.Option(
        None, "--config", "-c", help="Config YAML path"
    ),
    parallel: int = typer.Option(1, "--parallel", "-p", help="Number of parallel runs"),
    iter_count: int = typer.Option(1, "--iter", "-n", help="Number of iterations"),
):
    """Decompose a thesis into verifiable claims."""
    try:
        from aether.config import get_config
        from aether.config import resolve_path
        from aether.pipeline.runner import run_claim
        from aether.pipeline.runner import run_claim_parallel

        config = get_config(config_path)
        show_header(model=config.llm.model, ticker=config.data.ticker)
        output_path = output_dir or os.path.join(
            resolve_path(config.data.database_dir), "claim"
        )

        if not show_run_plan(
            "Claim Decomposition",
            parallel,
            iter_count,
            config=config,
            output_path=output_path,
            skip_confirm=_skip_confirm,
        ):
            show_closer("Cancelled")
            raise typer.Exit(code=0)

        total_count = 0
        total_start = time.time()

        for i in range(iter_count):
            iter_label = f"Iter {i + 1}/{iter_count}" if iter_count > 1 else None
            if parallel > 1:
                with step_progress(
                    f"Decomposing Claims ({parallel} parallel)", iter_label=iter_label
                ):
                    result = _run_async(
                        run_claim_parallel(
                            thesis_load_basedir=thesis_dir,
                            claim_save_basedir=output_dir,
                            num_parallel=parallel,
                        )
                    )
                count = len(result)  # each result is one (thesis, claims) pair
            else:
                with step_progress("Decomposing Claims", iter_label=iter_label):
                    run_claim(
                        thesis_load_basedir=thesis_dir,
                        claim_save_basedir=output_dir,
                    )
                count = 1
            total_count += count
            show_step_result(
                _pluralize(count, "claim set", "claim sets") + " generated"
            )

        total_time = time.time() - total_start
        show_summary(
            [
                ("Total", _pluralize(total_count, "claim set", "claim sets")),
                ("Time", _time_summary(total_time, iter_count)),
                ("Output", output_path),
            ]
        )
        show_closer(elapsed=total_time)
    except typer.Exit:
        raise
    except Exception as e:
        show_error_block("Claim Decomposition Failed", str(e), verbose=_verbose)
        raise typer.Exit(code=1)


@app.command()
def statement(
    claim_dir: str | None = typer.Option(None, "--claim-dir", help="Claims directory"),
    output_dir: str | None = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
    config_path: str | None = typer.Option(
        None, "--config", "-c", help="Config YAML path"
    ),
    parallel: int = typer.Option(1, "--parallel", "-p", help="Number of parallel runs"),
    iter_count: int = typer.Option(1, "--iter", "-n", help="Number of iterations"),
):
    """Verify claims and synthesize a statement."""
    try:
        from aether.config import get_config
        from aether.config import resolve_path
        from aether.pipeline.runner import run_statement
        from aether.pipeline.runner import run_statement_parallel

        config = get_config(config_path)
        show_header(model=config.llm.model, ticker=config.data.ticker)
        output_path = output_dir or os.path.join(
            resolve_path(config.data.database_dir), "statement"
        )

        if not show_run_plan(
            "Statement Synthesis",
            parallel,
            iter_count,
            config=config,
            output_path=output_path,
            skip_confirm=_skip_confirm,
        ):
            show_closer("Cancelled")
            raise typer.Exit(code=0)

        total_count = 0
        total_start = time.time()

        for i in range(iter_count):
            iter_label = f"Iter {i + 1}/{iter_count}" if iter_count > 1 else None
            if parallel > 1:
                with step_progress(
                    f"Verifying & Synthesizing ({parallel} parallel)",
                    iter_label=iter_label,
                ):
                    result = _run_async(
                        run_statement_parallel(
                            claim_load_basedir=claim_dir,
                            statement_save_basedir=output_dir,
                            num_parallel=parallel,
                        )
                    )
                count = len(result)
            else:
                with step_progress(
                    "Verifying & Synthesizing Statement", iter_label=iter_label
                ):
                    _run_async(
                        run_statement(
                            claim_load_basedir=claim_dir,
                            statement_save_basedir=output_dir,
                        )
                    )
                count = 1
            total_count += count
            show_step_result(
                _pluralize(count, "statement", "statements") + " generated"
            )

        total_time = time.time() - total_start
        show_summary(
            [
                ("Total", _pluralize(total_count, "statement", "statements")),
                ("Time", _time_summary(total_time, iter_count)),
                ("Output", output_path),
            ]
        )
        show_closer(elapsed=total_time)
    except typer.Exit:
        raise
    except Exception as e:
        show_error_block("Statement Generation Failed", str(e), verbose=_verbose)
        raise typer.Exit(code=1)


@app.command()
def factor(
    statement_dir: str | None = typer.Option(
        None, "--statement-dir", help="Statement directory"
    ),
    output_dir: str | None = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
    config_path: str | None = typer.Option(
        None, "--config", "-c", help="Config YAML path"
    ),
    parallel: int = typer.Option(1, "--parallel", "-p", help="Number of parallel runs"),
    iter_count: int = typer.Option(1, "--iter", "-n", help="Number of iterations"),
):
    """Generate factor code from a statement."""
    try:
        from aether.config import get_config
        from aether.config import resolve_path
        from aether.pipeline.runner import run_factor
        from aether.pipeline.runner import run_factor_parallel

        config = get_config(config_path)
        show_header(model=config.llm.model, ticker=config.data.ticker)
        output_path = output_dir or os.path.join(
            resolve_path(config.data.database_dir), "factor"
        )

        if not show_run_plan(
            "Factor Generation",
            parallel,
            iter_count,
            config=config,
            output_path=output_path,
            skip_confirm=_skip_confirm,
        ):
            show_closer("Cancelled")
            raise typer.Exit(code=0)

        total_count = 0
        total_start = time.time()

        for i in range(iter_count):
            iter_label = f"Iter {i + 1}/{iter_count}" if iter_count > 1 else None
            if parallel > 1:
                with step_progress(
                    f"Generating Factor ({parallel} parallel)", iter_label=iter_label
                ):
                    result = _run_async(
                        run_factor_parallel(
                            statement_load_basedir=statement_dir,
                            factor_save_basedir=output_dir,
                            num_parallel=parallel,
                        )
                    )
                count = len(result)
            else:
                with step_progress("Generating Factor", iter_label=iter_label):
                    run_factor(
                        statement_load_basedir=statement_dir,
                        factor_save_basedir=output_dir,
                    )
                count = 1
            total_count += count
            show_step_result(_pluralize(count, "factor", "factors") + " generated")

        total_time = time.time() - total_start
        show_summary(
            [
                ("Total", _pluralize(total_count, "factor", "factors")),
                ("Time", _time_summary(total_time, iter_count)),
                ("Output", output_path),
            ]
        )
        show_closer(elapsed=total_time)
    except typer.Exit:
        raise
    except Exception as e:
        show_error_block("Factor Generation Failed", str(e), verbose=_verbose)
        raise typer.Exit(code=1)


@app.command()
def backtest(
    factor_dir: str | None = typer.Option(
        None, "--factor-dir", help="Factor directory (JSON files)"
    ),
    output_dir: str | None = typer.Option(
        None, "--output", "-o", help="Backtest output directory"
    ),
    config_path: str | None = typer.Option(
        None, "--config", "-c", help="Config YAML path"
    ),
):
    """Backtest all factor JSON files and save metric/plot per factor."""
    try:
        from aether.config import get_config
        from aether.config import resolve_path
        from aether.pipeline.runner import run_backtest_batch

        config = get_config(config_path)
        show_header(model=config.llm.model, ticker=config.data.ticker)

        db_dir = resolve_path(config.data.database_dir)
        factor_path = factor_dir or os.path.join(db_dir, "factor")
        output_path = output_dir or os.path.join(db_dir, "backtest")

        if not show_run_plan(
            "Backtest Batch",
            config=config,
            output_path=output_path,
            skip_confirm=_skip_confirm,
        ):
            show_closer("Cancelled")
            raise typer.Exit(code=0)

        total_start = time.time()
        with step_progress("Running factor backtests"):
            summary = run_backtest_batch(
                factor_dir=factor_path,
                backtest_save_basedir=output_path,
            )

        total_time = time.time() - total_start
        show_step_result(
            f"processed={summary['processed']}, skipped={summary['skipped_existing']}, failed={summary['failed']}"
        )
        show_summary(
            [
                ("Total factors", str(summary["total"])),
                ("Processed", str(summary["processed"])),
                ("Skipped(existing)", str(summary["skipped_existing"])),
                ("Failed", str(summary["failed"])),
                ("Time", f"{total_time:.1f}s"),
                ("Output", output_path),
            ]
        )
        show_closer(elapsed=total_time)
    except typer.Exit:
        raise
    except Exception as e:
        show_error_block("Backtest Batch Failed", str(e), verbose=_verbose)
        raise typer.Exit(code=1)


@app.command("config")
def show_config(
    config_path: str | None = typer.Option(
        None, "--config", "-c", help="Config YAML path"
    ),
):
    """Show the current configuration."""
    from aether.config import get_config

    config = get_config(config_path)
    show_header()
    config_dict = asdict(config)
    # Mask API key
    if config_dict.get("llm", {}).get("api_key"):
        key = config_dict["llm"]["api_key"]
        config_dict["llm"]["api_key"] = (
            f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"
        )
    show_config_display(config_dict)
    show_closer()


def main():
    app()


if __name__ == "__main__":
    main()
