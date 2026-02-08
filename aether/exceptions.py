class AetherError(Exception):
    """Base exception for all AETHER errors."""


class ConfigError(AetherError):
    """Configuration-related errors."""


class DataError(AetherError):
    """Data loading or processing errors."""


class LLMError(AetherError):
    """LLM API call errors."""


class LLMTimeoutError(LLMError):
    """LLM API call timed out."""


class LLMParseError(LLMError):
    """Failed to parse LLM response into structured output."""


class PipelineError(AetherError):
    """Pipeline execution errors."""


class ClauseGenerationError(PipelineError):
    """Clause tree or graph generation failed."""


class AgentExecutionError(PipelineError):
    """An agent failed to produce a valid result."""
