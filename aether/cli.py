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
def run(
    config_path: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to config YAML file"
    ),
):
    """Run the full pipeline: clause -> thesis -> claim -> statement -> factor."""
    try:
        from aether.config import get_config
        from aether.pipeline.runner import run_full_pipeline

        config = get_config(config_path)
        show_header(model=config.llm.model, ticker=config.data.ticker)
        _, metrics = asyncio.run(run_full_pipeline(config))
        show_closer(f"Done in {metrics['duration']}")
    except Exception as e:
        show_error_block("Pipeline Failed", str(e))
        raise typer.Exit(code=1)


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
        from aether.config import get_config
        from entrypoints.generate_clause import main

        config = get_config(config_path)
        show_header(model=config.llm.model, ticker=config.data.ticker)
        with step_progress("Building Clause Graph"):
            main(version=version, clause_save_basedir=output_dir)
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
):
    """Generate a thesis from a ClauseGraph subgraph."""
    try:
        from aether.config import get_config
        from entrypoints.generate_thesis import main

        config = get_config(config_path)
        show_header(model=config.llm.model, ticker=config.data.ticker)
        with step_progress("Generating Thesis"):
            main(
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
):
    """Decompose a thesis into verifiable claims."""
    try:
        from aether.config import get_config
        from entrypoints.generate_claim import main

        config = get_config(config_path)
        show_header(model=config.llm.model, ticker=config.data.ticker)
        with step_progress("Decomposing Claims"):
            main(thesis_load_basedir=thesis_dir, claim_save_basedir=output_dir)
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
):
    """Verify claims and synthesize a statement."""
    try:
        from aether.config import get_config
        from entrypoints.generate_statement import main

        config = get_config(config_path)
        show_header(model=config.llm.model, ticker=config.data.ticker)
        with step_progress("Verifying & Synthesizing Statement"):
            asyncio.run(
                main(claim_load_basedir=claim_dir, statement_save_basedir=output_dir)
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
):
    """Generate factor code from a statement."""
    try:
        from aether.config import get_config
        from entrypoints.generate_factor import main

        config = get_config(config_path)
        show_header(model=config.llm.model, ticker=config.data.ticker)
        with step_progress("Generating Factor"):
            main(statement_load_basedir=statement_dir, factor_save_basedir=output_dir)
        show_closer("Done")
    except Exception as e:
        show_error_block("Factor Generation Failed", str(e))
        raise typer.Exit(code=1)


@app.command()
def parallel(
    num_pipelines: int = typer.Option(
        4, "--num", "-n", help="Number of parallel pipelines"
    ),
    config_path: Optional[str] = typer.Option(
        None, "--config", "-c", help="Config YAML path"
    ),
):
    """Run multiple hypothesis pipelines in parallel using Ray."""
    try:
        from aether.config import get_config
        from aether.pipeline.parallel import run_parallel

        config = get_config(config_path)
        show_header(
            model=config.llm.model,
            ticker=config.data.ticker,
            pipelines=num_pipelines,
        )
        cfg_path = config_path or "config/aether.yaml"
        with step_progress(f"Running {num_pipelines} pipelines"):
            results = run_parallel(
                num_pipelines=num_pipelines, config=config, config_path=cfg_path
            )
        succeeded = sum(1 for r in results if "error" not in r)
        show_closer(f"Done — {succeeded}/{len(results)} pipelines succeeded")
    except Exception as e:
        show_error_block("Parallel Pipeline Failed", str(e))
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
