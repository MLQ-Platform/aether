# AETHER

**Data-driven Hypothesis Generation Engine** for quantitative market analysis.

AETHER automatically generates trading factor hypotheses from cryptocurrency market data through an LLM-powered multi-stage pipeline:

```
Random Indicator Trees → Statistical Dependency Graph → Thesis → Claims
→ Empirical Verification → Statement → Mathematical Proof → Factor Code
```

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Yang-Hyun-Jun/aether.git
cd aether

# Install dependencies
poetry install

# (Optional) Install with Ray for parallel execution
poetry install -E parallel
```

### Configuration

1. Set your API key:

```bash
# Create config/.env
echo "OPENROUTER_API_KEY=your-key-here" > config/.env
```

2. (Optional) Customize settings in `config/aether.yaml`:

```yaml
llm:
  model: "deepseek/deepseek-v3.2-exp"
  timeout: 120.0

pipeline:
  total_iterations: 4
  max_concurrent_requests: 5

data:
  ticker: "BTCUSDT"
  end_date: "2025-01-01"
```

3. Place your market data (parquet files) in `data/`.

### Usage

#### CLI

```bash
# Run the full pipeline
aether run

# Run individual stages
aether clause                    # Generate indicator tree graph
aether thesis                    # Generate causal hypothesis
aether claim                     # Decompose into verifiable claims
aether statement                 # Verify claims & synthesize statement
aether factor                    # Generate mathematical proof & code

# Run multiple pipelines in parallel (requires Ray)
aether parallel --num 4

# Show current configuration
aether config

# Use a custom config file
aether run --config path/to/config.yaml
```

#### Python API

```python
import asyncio
from aether.pipeline.runner import run_full_pipeline
from aether.config import Config

# With default config
result = asyncio.run(run_full_pipeline())

# With custom config
config = Config.from_yaml("my_config.yaml")
result = asyncio.run(run_full_pipeline(config))
```

## Architecture

### Pipeline Stages

| Stage | Module | Description |
|-------|--------|-------------|
| 1. Clause | `aether/clause/` | Randomly generates hierarchical indicator trees (`ClauseTree`) and assembles them into a `ClauseGraph` with edges weighted by Symmetric Uncertainty |
| 2. Thesis | `aether/agents/thesis/` | Takes two statistically related trees from a subgraph and generates a causal market hypothesis |
| 3. Claim | `aether/agents/claim/` | Decomposes a thesis into atomic, verifiable claims |
| 4. Rationale | `aether/agents/rationale/` | ReAct agent that executes Python code against market DataFrames to empirically verify each claim |
| 5. Statement | `aether/agents/statement/` | Aggregates verified claims into a coherent statement with provenance tracking |
| 6. Factor | `aether/agents/factor/` | Converts statement into mathematical proof, validates, and generates executable Python code |

### Project Structure

```
aether/
├── agents/          # LLM agent implementations (thesis, claim, rationale, statement, factor)
├── clause/          # Indicator tree generation and graph analysis
├── llm/             # LLM layer (BaseLLM, StructuredLLM, ReactAgent)
├── pipeline/        # Pipeline stage functions and orchestration
├── prompts/         # System prompt templates
├── provider/        # Market data loading
├── cli.py           # Typer CLI interface
├── config.py        # Centralized configuration
├── exceptions.py    # Custom exception hierarchy
├── factory.py       # Agent/client factory
└── utils.py         # UUID generation, JSON I/O
config/
├── aether.yaml      # Main configuration file
├── schema.yaml      # Market data column definitions
└── .env             # API keys (not committed)
tests/               # pytest test suite
```

## Configuration Reference

All settings in `config/aether.yaml`:

| Section | Key | Default | Description |
|---------|-----|---------|-------------|
| `llm.model` | string | `deepseek/deepseek-v3.2-exp` | LLM model name |
| `llm.base_url` | string | `https://openrouter.ai/api/v1` | API endpoint |
| `llm.timeout` | float | `120.0` | Per-call timeout (seconds) |
| `llm.max_retries` | int | `3` | Auto-retry on 429/5xx |
| `pipeline.total_iterations` | int | `4` | Claim verification rounds |
| `pipeline.revision_iterations` | int | `3` | Proof revision rounds |
| `pipeline.max_concurrent_requests` | int | `5` | Max concurrent LLM calls |
| `clause.num_trees` | int | `10` | Trees per generation batch |
| `clause.max_depth` | int | `3` | Max tree depth |
| `clause.period` | int | `10` | Rolling window period |
| `data.ticker` | string | `BTCUSDT` | Target trading pair |
| `data.end_date` | string | `2025-01-01` | Data cutoff date |

## Development

```bash
# Install dev dependencies
poetry install --with dev

# Run tests
pytest

# Lint & format
ruff check .
ruff format .
```

## License

MIT
