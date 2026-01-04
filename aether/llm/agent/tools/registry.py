from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from aether.llm.agent.tools.base import Tool


class ToolRegistry:
    """
    Tool 레지스트리
    """

    def __init__(self):
        self._tools: Dict[str, Dict[str, Tool]] = {}

    def get_agent_names(self) -> List[str]:
        """
        등록된 agent 이름 리스트 조회
        """
        return list(self._tools.keys())

    def get_tools(self, agent_name: str) -> List[Tool]:
        """
        특정 agent의 Tool 리스트 조회
        """
        return list(self._tools.get(agent_name, {}).values())

    def get_tool_names(self, agent_name: str) -> List[str]:
        """
        특정 agent의 Tool 이름 리스트 조회
        """
        return list(self._tools.get(agent_name, {}).keys())

    def register(self, tool: Tool, agent_name: str) -> None:
        """
        Tool 등록
        """
        if agent_name not in self._tools:
            self._tools[agent_name] = {}
        self._tools[agent_name][tool.name] = tool

    def get(self, name: str, agent_name: str) -> Optional[Tool]:
        """
        Tool 조회
        """
        return self._tools.get(agent_name, {}).get(name)

    def decorator(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        agent_name: str,
    ):
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
                },
                agent_name="math"
            )
            def add(a: float, b: float) -> float:
                return a + b
        """

        def wrapper(func: Callable) -> Callable:
            tool = Tool(
                name=name, description=description, func=func, parameters=parameters
            )
            self.register(tool, agent_name=agent_name)
            return func

        return wrapper
