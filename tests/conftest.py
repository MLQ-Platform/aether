import pytest
from aether.config import Config
from aether.config import LLMConfig
from aether.config import PipelineConfig
from aether.config import ClauseConfig
from aether.config import DataConfig
from aether.config import AgentConfig
from aether.config import reset_config


@pytest.fixture(autouse=True)
def _reset_config():
    """Reset global config singleton between tests."""
    reset_config()
    yield
    reset_config()


@pytest.fixture
def config():
    """Create a test config with defaults (no YAML loading)."""
    return Config(
        llm=LLMConfig(api_key="test-key"),
        pipeline=PipelineConfig(total_iterations=2, revision_iterations=1),
        clause=ClauseConfig(num_trees=3, max_depth=2, num_edges=5, max_iterations=10),
        data=DataConfig(),
        agent=AgentConfig(react_max_iterations=3, tool_timeout=30),
    )
