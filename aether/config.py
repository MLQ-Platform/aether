from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
import yaml

# Project root: aether/ package parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resolve_path(path: str) -> str:
    """Resolve a relative path against the project root."""
    p = Path(path)
    if p.is_absolute():
        return str(p)
    return str(PROJECT_ROOT / p)


@dataclass
class LLMConfig:
    model: str = "deepseek/deepseek-v3.2-exp"
    base_url: str = "https://openrouter.ai/api/v1"
    api_key: str | None = None
    timeout: float = 120.0
    max_retries: int = 3
    parse_retries: int = 5


@dataclass
class PipelineConfig:
    total_iterations: int = 2
    revision_iterations: int = 3
    max_workers: int = 5


@dataclass
class ClauseConfig:
    num_trees: int = 10
    max_depth: int = 3
    period: int = 10
    num_edges: int = 50
    max_iterations: int = 1000
    tree_max_iter: int = 20
    restart_prob: float = 0.1
    length_factor: float = 2.0
    sim_threshold: float = 0.2
    weight_threshold: float = 0.05
    min_signal_ratio: float = 0.10
    max_signal_ratio: float = 0.50


@dataclass
class DataConfig:
    ticker: str = "BTCUSDT"
    end_date: str = "2025-01-01"
    data_dir: str = "data"
    database_dir: str = "database"


@dataclass
class AgentConfig:
    react_max_iterations: int = 4
    tool_timeout: int = 180


@dataclass
class Config:
    llm: LLMConfig = field(default_factory=LLMConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    clause: ClauseConfig = field(default_factory=ClauseConfig)
    data: DataConfig = field(default_factory=DataConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)

    def __post_init__(self):
        import os
        import dotenv

        dotenv.load_dotenv(dotenv_path=resolve_path("config/.env"))

        if self.llm.api_key is None:
            self.llm.api_key = os.getenv("OPENROUTER_API_KEY")

    @classmethod
    def from_yaml(cls, path: str = "config/aether.yaml") -> "Config":
        config_path = Path(resolve_path(path))

        if not config_path.exists():
            return cls()

        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

        return cls(
            llm=LLMConfig(**data.get("llm", {})),
            pipeline=PipelineConfig(**data.get("pipeline", {})),
            clause=ClauseConfig(**data.get("clause", {})),
            data=DataConfig(**data.get("data", {})),
            agent=AgentConfig(**data.get("agent", {})),
        )


_config: Config | None = None


def get_config(path: str | None = None) -> Config:
    global _config
    if _config is None:
        _config = Config.from_yaml(path) if path else Config.from_yaml()
    return _config


def reset_config():
    global _config
    _config = None


class DataSchema:
    """
    Data schema configuration loader for schema.yaml
    """

    def __init__(self, config_path: str = "config/schema.yaml"):
        self.config_path = Path(resolve_path(config_path))
        self.data_schema = self._load()

    def _load(self) -> dict:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.config_path}")

        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def get_index_info(self) -> dict:
        return self.data_schema.get("index", {})

    def get_description(self, with_index: bool = False) -> str:
        lines = ["Available Data Columns:"]

        columns = self.data_schema.get("columns", {})

        for col_name, col_info in columns.items():
            col_desc = col_info.get("description", "")
            col_type = col_info.get("type", "")
            lines.append(f"  - {col_name} ({col_type}): {col_desc}")

        if with_index:
            lines.append("\nIndex:")
            index_info = self.get_index_info()
            index_name = index_info.get("name", "")
            index_type = index_info.get("type", "")
            index_desc = index_info.get("description", "")
            lines.append(f"  - {index_name} ({index_type}): {index_desc}")

        return "\n".join(lines)
