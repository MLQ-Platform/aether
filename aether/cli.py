import asyncio
from dataclasses import asdict
from typing import Optional
import typer
from aether.display import show_closer
from aether.display import show_config_display
from aether.display import show_error_block
from aether.display import show_header
from aether.display import step_progress

app = typer.Typer(
    name="aether",
    help="AETHER - Data-driven Hypothesis Generation Engine",
    add_completion=False,
)

_verbose = False


@app.callback()
def callback(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
):
    """AETHER - Data-driven Hypothesis Generation Engine"""
    global _verbose
    _verbose = verbose
    from aether.logger import init_cli

    init_cli(verbose)


@app.command()
def clause(
    version: str = typer.Option("v0", "--version", help="Clause graph version tag"),
    output_dir: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
    config_path: Optional[str] = typer.Option(
        None, "--config", "-c", help="Config YAML path"
    ),
):
    """Generate a ClauseGraph from random indicator trees."""
    try:
        import os
        from aether.config import get_config
        from aether.config import resolve_path
        from aether.pipeline.clause import build_clause_graph

        config = get_config(config_path)
        show_header(model=config.llm.model, ticker=config.data.ticker)
        with step_progress("Building Clause Graph") as ctx:
            clause_graph = build_clause_graph(
                config, on_progress=lambda e, i: ctx.update(f"{e} edges")
            )
            ctx.detail(
                f"{clause_graph.num_nodes} nodes, {clause_graph.num_edges} edges"
            )
        save_dir = output_dir or os.path.join(
            resolve_path(config.data.database_dir), "clause"
        )
        os.makedirs(save_dir, exist_ok=True)
        clause_graph.save(os.path.join(save_dir, f"clause-{version}.json"))
        show_closer("Done")
    except Exception as e:
        show_error_block("Clause Generation Failed", str(e))
        raise typer.Exit(code=1)


@app.command()
def thesis(
    clause_version: str = typer.Option(
        "v0", "--clause-version", help="Clause graph version to load"
    ),
    clause_dir: Optional[str] = typer.Option(
        None, "--clause-dir", help="Clause graph directory"
    ),
    output_dir: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
    config_path: Optional[str] = typer.Option(
        None, "--config", "-c", help="Config YAML path"
    ),
    parallel: int = typer.Option(1, "--parallel", "-p", help="Number of parallel runs"),
    iter_count: int = typer.Option(1, "--iter", "-n", help="Number of iterations"),
):
    """Generate a thesis from a ClauseGraph subgraph."""
    try:
        from aether.config import get_config
        from aether.pipeline.runner import run_thesis
        from aether.pipeline.runner import run_thesis_parallel

        config = get_config(config_path)
        show_header(model=config.llm.model, ticker=config.data.ticker)
        for i in range(iter_count):
            label = f" (iter {i + 1}/{iter_count})" if iter_count > 1 else ""
            if parallel > 1:
                with step_progress(f"Generating {parallel} Theses (parallel){label}"):
                    asyncio.run(
                        run_thesis_parallel(
                            clause_load_basedir=clause_dir,
                            thesis_save_basedir=output_dir,
                            clause_version=clause_version,
                            num_parallel=parallel,
                        )
                    )
            else:
                with step_progress(f"Generating Thesis{label}"):
                    run_thesis(
                        clause_load_basedir=clause_dir,
                        thesis_save_basedir=output_dir,
                        clause_version=clause_version,
                    )
        show_closer("Done")
    except Exception as e:
        show_error_block("Thesis Generation Failed", str(e))
        raise typer.Exit(code=1)


@app.command()
def claim(
    thesis_dir: Optional[str] = typer.Option(
        None, "--thesis-dir", help="Thesis directory"
    ),
    output_dir: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
    config_path: Optional[str] = typer.Option(
        None, "--config", "-c", help="Config YAML path"
    ),
    parallel: int = typer.Option(1, "--parallel", "-p", help="Number of parallel runs"),
    iter_count: int = typer.Option(1, "--iter", "-n", help="Number of iterations"),
):
    """Decompose a thesis into verifiable claims."""
    try:
        from aether.config import get_config
        from aether.pipeline.runner import run_claim
        from aether.pipeline.runner import run_claim_parallel

        config = get_config(config_path)
        show_header(model=config.llm.model, ticker=config.data.ticker)
        for i in range(iter_count):
            label = f" (iter {i + 1}/{iter_count})" if iter_count > 1 else ""
            if parallel > 1:
                with step_progress(f"Decomposing Claims ({parallel} parallel){label}"):
                    asyncio.run(
                        run_claim_parallel(
                            thesis_load_basedir=thesis_dir,
                            claim_save_basedir=output_dir,
                            num_parallel=parallel,
                        )
                    )
            else:
                with step_progress(f"Decomposing Claims{label}"):
                    run_claim(
                        thesis_load_basedir=thesis_dir,
                        claim_save_basedir=output_dir,
                    )
        show_closer("Done")
    except Exception as e:
        show_error_block("Claim Decomposition Failed", str(e))
        raise typer.Exit(code=1)


@app.command()
def statement(
    claim_dir: Optional[str] = typer.Option(
        None, "--claim-dir", help="Claims directory"
    ),
    output_dir: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
    config_path: Optional[str] = typer.Option(
        None, "--config", "-c", help="Config YAML path"
    ),
    parallel: int = typer.Option(1, "--parallel", "-p", help="Number of parallel runs"),
    iter_count: int = typer.Option(1, "--iter", "-n", help="Number of iterations"),
):
    """Verify claims and synthesize a statement."""
    try:
        from aether.config import get_config
        from aether.pipeline.runner import run_statement
        from aether.pipeline.runner import run_statement_parallel

        config = get_config(config_path)
        show_header(model=config.llm.model, ticker=config.data.ticker)
        for i in range(iter_count):
            label = f" (iter {i + 1}/{iter_count})" if iter_count > 1 else ""
            if parallel > 1:
                with step_progress(
                    f"Verifying & Synthesizing Statement ({parallel} parallel){label}"
                ):
                    asyncio.run(
                        run_statement_parallel(
                            claim_load_basedir=claim_dir,
                            statement_save_basedir=output_dir,
                            num_parallel=parallel,
                        )
                    )
            else:
                with step_progress(f"Verifying & Synthesizing Statement{label}"):
                    asyncio.run(
                        run_statement(
                            claim_load_basedir=claim_dir,
                            statement_save_basedir=output_dir,
                        )
                    )
        show_closer("Done")
    except Exception as e:
        show_error_block("Statement Generation Failed", str(e))
        raise typer.Exit(code=1)


@app.command()
def factor(
    statement_dir: Optional[str] = typer.Option(
        None, "--statement-dir", help="Statement directory"
    ),
    output_dir: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
    config_path: Optional[str] = typer.Option(
        None, "--config", "-c", help="Config YAML path"
    ),
    parallel: int = typer.Option(1, "--parallel", "-p", help="Number of parallel runs"),
    iter_count: int = typer.Option(1, "--iter", "-n", help="Number of iterations"),
):
    """Generate factor code from a statement."""
    try:
        from aether.config import get_config
        from aether.pipeline.runner import run_factor
        from aether.pipeline.runner import run_factor_parallel

        config = get_config(config_path)
        show_header(model=config.llm.model, ticker=config.data.ticker)
        for i in range(iter_count):
            label = f" (iter {i + 1}/{iter_count})" if iter_count > 1 else ""
            if parallel > 1:
                with step_progress(f"Generating Factor ({parallel} parallel){label}"):
                    asyncio.run(
                        run_factor_parallel(
                            statement_load_basedir=statement_dir,
                            factor_save_basedir=output_dir,
                            num_parallel=parallel,
                        )
                    )
            else:
                with step_progress(f"Generating Factor{label}"):
                    run_factor(
                        statement_load_basedir=statement_dir,
                        factor_save_basedir=output_dir,
                    )
        show_closer("Done")
    except Exception as e:
        show_error_block("Factor Generation Failed", str(e))
        raise typer.Exit(code=1)


@app.command("config")
def show_config(
    config_path: Optional[str] = typer.Option(
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


def main():
    app()


if __name__ == "__main__":
    main()
