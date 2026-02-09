from typing import Any
from typing import Callable
from typing import Dict
from pydantic import BaseModel
from pydantic import Field


class Tool(BaseModel):
    """
    범용 Tool 정의

    LLM이 호출할 수 있는 도구(함수)를 정의합니다.

    Example:
        def search_web(query: str) -> str:
            return f"Search results for: {query}"

        tool = Tool(
            name="search_web",
            description="Search the web for information",
            func=search_web,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        )
    """

    name: str = Field(description="도구 이름")
    description: str = Field(description="도구 설명")
    func: Callable = Field(description="실제 실행할 함수")
    parameters: Dict[str, Any] = Field(description="JSON Schema 형식의 파라미터")

    class Config:
        arbitrary_types_allowed = True
