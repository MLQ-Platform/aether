from pprint import PrettyPrinter
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from aether.llm.agent.tools.base import Tool


class ToolRegistry:
    """
    Tool 레지스트리

    여러 Tool을 관리하고 쉽게 등록/조회할 수 있는 유틸리티
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    @property
    def tools(self) -> List[Tool]:
        """
        Tool 리스트 조회
        """
        return list(self._tools.values())

    @property
    def names(self) -> List[str]:
        """
        Tool 이름 리스트 조회
        """
        return list(self._tools.keys())

    def register(self, tool: Tool) -> None:
        """
        Tool 등록
        """
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """
        Tool 조회
        """
        return self._tools.get(name)

    def decorator(self, name: str, description: str, parameters: Dict[str, Any]):
        """
        데코레이터로 Tool 등록

        Example:
            registry = ToolRegistry()

            @registry.decorator(
                name="add",
                description="Add two numbers",
                parameters={
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"}
                    },
                    "required": ["a", "b"]
                }
            )
            def add(a: float, b: float) -> float:
                return a + b
        """

        def wrapper(func: Callable) -> Callable:
            tool = Tool(
                name=name, description=description, func=func, parameters=parameters
            )
            self.register(tool)
            return func

        return wrapper


# 전역 레지스트리 인스턴스
registry = ToolRegistry()
