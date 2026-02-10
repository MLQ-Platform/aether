from typing import Any
from typing import Callable
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class Tool(BaseModel):
    """Tool definition for LLM function calling."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    func: Callable = Field(description="Callable to execute")
    parameters: dict[str, Any] = Field(description="JSON Schema parameters")
