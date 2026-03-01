import os
import tempfile
import pytest
import yaml
from aether.config import Config
from aether.config import LLMConfig
from aether.config import PipelineConfig
from aether.config import ClauseConfig
from aether.config import DataConfig
from aether.config import AgentConfig
from aether.config import get_config
from aether.config import reset_config


class TestConfig:
    def test_default_config(self, config):
        assert config.llm.model == "deepseek/deepseek-v3.2-exp"
        assert config.llm.timeout == 120.0
        assert config.llm.max_retries == 3
        assert config.pipeline.total_iterations == 2
        assert config.clause.num_trees == 3
        assert config.data.ticker == "BTCUSDT"
        assert config.agent.react_max_iterations == 3

    def test_config_from_yaml(self, tmp_path):
        config_data = {
            "llm": {"model": "gpt-4o", "timeout": 60.0},
            "pipeline": {"total_iterations": 10},
            "data": {"ticker": "ETHUSDT"},
        }
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(yaml.dump(config_data))

        config = Config.from_yaml(str(config_file))

        assert config.llm.model == "gpt-4o"
        assert config.llm.timeout == 60.0
        # Defaults preserved for unspecified fields
        assert config.llm.max_retries == 3
        assert config.pipeline.total_iterations == 10
        assert config.data.ticker == "ETHUSDT"
        # Unspecified sections use defaults
        assert config.clause.num_trees == 10
        assert config.agent.react_max_iterations == 10

    def test_config_from_yaml_missing_file(self):
        config = Config.from_yaml("/nonexistent/path.yaml")
        # Should return default config
        assert config.llm.model == "deepseek/deepseek-v3.2-exp"

    def test_config_from_yaml_empty_file(self, tmp_path):
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        config = Config.from_yaml(str(config_file))
        assert config.llm.model == "deepseek/deepseek-v3.2-exp"

    def test_get_config_singleton(self, tmp_path):
        config_data = {"llm": {"model": "test-model"}}
        config_file = tmp_path / "singleton.yaml"
        config_file.write_text(yaml.dump(config_data))

        config1 = get_config(str(config_file))
        config2 = get_config()  # Should return cached

        assert config1 is config2
        assert config1.llm.model == "test-model"

    def test_get_config_reload_on_explicit_path(self, tmp_path):
        config_a = tmp_path / "a.yaml"
        config_b = tmp_path / "b.yaml"
        config_a.write_text(yaml.dump({"llm": {"model": "model-a"}}))
        config_b.write_text(yaml.dump({"llm": {"model": "model-b"}}))

        loaded_a = get_config(str(config_a))
        loaded_b = get_config(str(config_b))

        assert loaded_a.llm.model == "model-a"
        assert loaded_b.llm.model == "model-b"
        assert loaded_a is not loaded_b

    def test_nested_dataclass_structure(self):
        config = Config()
        assert isinstance(config.llm, LLMConfig)
        assert isinstance(config.pipeline, PipelineConfig)
        assert isinstance(config.clause, ClauseConfig)
        assert isinstance(config.data, DataConfig)
        assert isinstance(config.agent, AgentConfig)


class TestDataSchema:
    def test_load_schema(self):
        from aether.config import DataSchema

        # This test only works when schema.yaml exists
        if os.path.exists("config/schema.yaml"):
            schema = DataSchema()
            desc = schema.get_description()
            assert "CLOSE" in desc
            assert "VOLUME" in desc

    def test_schema_file_not_found(self):
        from aether.config import DataSchema

        with pytest.raises(FileNotFoundError):
            DataSchema(config_path="/nonexistent/schema.yaml")
