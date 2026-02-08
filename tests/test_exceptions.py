from aether.exceptions import AetherError
from aether.exceptions import LLMError
from aether.exceptions import LLMTimeoutError
from aether.exceptions import LLMParseError
from aether.exceptions import PipelineError
from aether.exceptions import ClauseGenerationError
from aether.exceptions import AgentExecutionError
from aether.exceptions import ConfigError
from aether.exceptions import DataError


class TestExceptionHierarchy:
    def test_base_exception(self):
        assert issubclass(AetherError, Exception)

    def test_llm_exceptions(self):
        assert issubclass(LLMError, AetherError)
        assert issubclass(LLMTimeoutError, LLMError)
        assert issubclass(LLMParseError, LLMError)

    def test_pipeline_exceptions(self):
        assert issubclass(PipelineError, AetherError)
        assert issubclass(ClauseGenerationError, PipelineError)
        assert issubclass(AgentExecutionError, PipelineError)

    def test_other_exceptions(self):
        assert issubclass(ConfigError, AetherError)
        assert issubclass(DataError, AetherError)

    def test_catch_all_with_base(self):
        try:
            raise LLMTimeoutError("timeout")
        except AetherError as e:
            assert str(e) == "timeout"

    def test_catch_llm_group(self):
        try:
            raise LLMParseError("bad json")
        except LLMError as e:
            assert str(e) == "bad json"
