# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AETHER is a **Data-driven Hypothesis Generation Engine** for quantitative market analysis. It automatically generates trading factor hypotheses from cryptocurrency market data through an LLM-powered multi-stage pipeline:

**Random Indicator Trees → Statistical Dependency Graph → Thesis → Claims → Empirical Verification → Statement → Mathematical Proof → Factor Code**

## Commands

```bash
# Install dependencies
poetry install

# Run the full pipeline
python main.py

# Run individual pipeline stages
python entrypoints/generate_clause.py
python entrypoints/generate_thesis.py
python entrypoints/generate_claim.py
python entrypoints/generate_statement.py
python entrypoints/generate_factor.py

# Lint
ruff check .
ruff format .
```

No test framework is currently configured.

## Configuration

- **LLM API**: Uses OpenRouter (OpenAI-compatible). Set `OPENROUTER_API_KEY` in `config/.env`.
- **Data Schema**: `config/schema.yaml` defines market data columns (OHLCV, premium index, order flow, funding).
- **Default Model**: `deepseek/deepseek-v3.2-exp` (configurable per agent in `aether/factory.py`).

## Architecture

### Pipeline Stages (in order)

1. **Clause Generation** (`aether/clause/`): Randomly generates `ClauseTree` structures — hierarchical trees where leaves are raw market data columns and internal nodes are mathematical transformations (SMA, STD, DIFF, ZSCORE, etc.). Trees are assembled into a `ClauseGraph` with edges weighted by Symmetric Uncertainty.

2. **Thesis Generation** (`aether/agents/thesis/`): Takes two statistically related ClauseTrees from a subgraph and uses an LLM to generate a causal market hypothesis explaining their relationship.

3. **Claim Decomposition** (`aether/agents/claim/`): Decomposes a thesis into atomic, verifiable claims via LLM.

4. **Rationale / Verification** (`aether/agents/rationale/`): Uses a **ReAct agent** (`aether/llm/agent/react.py`) that iteratively executes Python code against market DataFrames to empirically verify each claim with statistical tests. Rejected claims are refined by `ClaimModifyAgent` and re-verified (up to `TOTAL_ITERATIONS` rounds in `main.py`).

5. **Statement Synthesis** (`aether/agents/statement/`): Aggregates verified claims into a coherent statement. Uses `StatementGraph` (a DAG tracking provenance: Thesis → Claims → Rationales → Modified Claims).

6. **Factor Generation** (`aether/agents/factor/`): Converts the statement into a mathematical proof (`InitialFactorStatementAgent`), validates it (`ProofCheckAgent`), fixes issues (`ProofFixAgent`), and generates executable Python code (`FactorCodeAgent`).

### Key Infrastructure

- **LLM Layer** (`aether/llm/`): `BaseLLM` wraps the OpenAI client. `StructuredLLM` generates validated Pydantic models with retry logic. `ReactAgent` implements the ReAct loop for tool-calling agents.
- **Factory** (`aether/factory.py`): Central creation point for all agents and clients. All agents are instantiated here with their model, client, and system prompt.
- **Data Provider** (`aether/provider/`): `InMemoryDataProvider` loads all parquet files from `data/` into memory at init.
- **System Prompts** (`aether/prompts/`): Text files containing detailed LLM instructions for each agent role.
- **All agent outputs are Pydantic models** with UUID fields for provenance tracking across the pipeline.

### Async Pattern

The rationale verification and claim modification stages run concurrently using `asyncio.gather`. These agents use `AsyncOpenAI` clients (created via `factory.get_async_client()`).

## Ruff Configuration

- Ignores `F401` (unused imports) and `I001` (isort order).
- Isort: `force-single-line = true`, no blank lines between import sections.
