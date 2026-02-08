# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AETHER is a **Data-driven Hypothesis Generation Engine** for quantitative market analysis. It automatically generates trading factor hypotheses from cryptocurrency market data through an LLM-powered multi-stage pipeline:

**Random Indicator Trees → Statistical Dependency Graph → Thesis → Claims → Empirical Verification → Statement → Mathematical Proof → Factor Code**

## Commands

```bash
# Install dependencies
poetry install

# CLI (after poetry install)
aether clause                    # Generate clause graph
aether thesis                    # Generate thesis
aether claim                     # Decompose claims
aether statement                 # Verify & synthesize statement
aether factor                    # Generate factor code
aether config                    # Show current config

# Legacy entrypoints (still work)
python entrypoints/generate_clause.py
python entrypoints/generate_thesis.py
python entrypoints/generate_claim.py
python entrypoints/generate_statement.py
python entrypoints/generate_factor.py

# Tests
pytest

# Lint
ruff check .
ruff format .
```

## Configuration

- **Centralized config**: `config/aether.yaml` — all settings in one place (LLM, pipeline, clause, data, agent parameters).
- **Config class**: `aether/config.py` — nested dataclasses (`Config.llm`, `Config.pipeline`, `Config.clause`, `Config.data`, `Config.agent`).
- **Singleton**: Use `get_config()` to access the cached config instance. Use `reset_config()` for testing.
- **LLM API**: Uses OpenRouter (OpenAI-compatible). Set `OPENROUTER_API_KEY` in `config/.env`.
- **Data Schema**: `config/schema.yaml` defines market data columns.

## Architecture

### Pipeline Stages (in order)

1. **Clause Generation** (`aether/clause/`, `aether/pipeline/clause.py`): Randomly generates `ClauseTree` structures — hierarchical trees where leaves are raw market data columns and internal nodes are mathematical transformations. Trees are assembled into a `ClauseGraph` with edges weighted by Symmetric Uncertainty.

2. **Thesis Generation** (`aether/agents/thesis/`, `aether/pipeline/thesis.py`): Takes two statistically related ClauseTrees from a subgraph and uses an LLM to generate a causal market hypothesis.

3. **Claim Decomposition** (`aether/agents/claim/`, `aether/pipeline/claim.py`): Decomposes a thesis into atomic, verifiable claims via LLM.

4. **Rationale / Verification** (`aether/agents/rationale/`, `aether/pipeline/statement.py`): Uses a **ReAct agent** (`aether/llm/agent/react.py`) that iteratively executes Python code against market DataFrames to empirically verify each claim. Rejected claims are refined by `ClaimModifyAgent` and re-verified.

5. **Statement Synthesis** (`aether/agents/statement/`, `aether/pipeline/statement.py`): Aggregates verified claims into a coherent statement. Uses `StatementGraph` for provenance tracking.

6. **Factor Generation** (`aether/agents/factor/`, `aether/pipeline/factor.py`): Converts the statement into a mathematical proof, validates it, fixes issues, and generates executable Python code.

### Key Modules

- **`aether/pipeline/`**: Consolidated pipeline logic for each stage (clause, thesis, claim, statement, factor).
- **`aether/llm/`**: `BaseLLM` wraps the OpenAI client. `StructuredLLM` generates validated Pydantic models with retry logic. `ReactAgent` implements the ReAct loop for tool-calling agents.
- **`aether/factory.py`**: Central creation point for all agents and clients. All factory functions accept an optional `Config` parameter (defaults to `get_config()`).
- **`aether/cli.py`**: Typer-based CLI. Entry point registered as `aether` in `pyproject.toml`.
- **`aether/exceptions.py`**: Custom exception hierarchy (`AetherError` → `LLMError`, `PipelineError`, `ConfigError`, `DataError`).
- **`aether/provider/`**: `InMemoryDataProvider` loads parquet files from `data/` into memory.

### Async & Concurrency

- Rationale verification and claim modification run concurrently using `asyncio.gather` with `asyncio.Semaphore` to limit concurrent LLM requests (configurable via `pipeline.max_concurrent_requests`).
- OpenAI client has built-in timeout + exponential backoff retry for 429/5xx errors (via `llm.timeout` and `llm.max_retries`).

## CLI Usage

The CLI uses a clack-style interactive UI with spinners. Loguru logs are suppressed by default; only the display layer renders output. Use `-v` for verbose debug logs.

```bash
# Pipeline stages (each shows a spinner while processing)
aether clause                    # Build clause graph (saved to database/clause/)
aether clause --version v1       # Tag the clause graph version
aether thesis                    # Generate thesis from clause graph v0
aether thesis --clause-version v1  # Use specific clause graph version
aether claim                     # Decompose thesis into claims
aether statement                 # Verify claims + synthesize statement
aether factor                    # Generate factor code from statement

# Config
aether config                    # Show current config in tree format

# All commands support:
#   -v, --verbose    Show DEBUG-level logs
#   -c, --config     Custom config YAML path
```

## Ruff Configuration

- Ignores `F401` (unused imports) and `I001` (isort order).
- Isort: `force-single-line = true`, no blank lines between import sections.
