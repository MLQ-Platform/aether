from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from aether.llm.agent.tools import Tool
from aether.llm.agent.tools import ToolCallAdapter


class ReactAgent:
    """
    ReAct Agent

    LLM이 도구를 사용하여 작업을 수행하는 에이전트입니다.
    ReAct 패턴: Reasoning (추론) + Acting (행동)

    사용법:
        from openai import OpenAI
        from aether.llm.agent import ReactAgent, Tool, OpenAIToolCallAdapter

        # Tool 정의
        def search(query: str) -> str:
            return f"Search results for: {query}"

        tools = [
            Tool(
                name="search",
                description="Search the web",
                func=search,
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            )
        ]

        # Agent 생성
        client = OpenAI(api_key="...")
        adapter = OpenAIToolCallAdapter(client)
        agent = ReactAgent(adapter, tools, model="gpt-4o-mini")

        # 실행
        result = agent.run("What is the weather?")
    """

    def __init__(
        self,
        adapter: ToolCallAdapter,
        tools: List[Tool],
        model: str,
        max_iterations: int = 10,
        verbose: bool = False,
    ):
        """
        Args:
            adapter: ToolCallAdapter (예: OpenAIToolCallAdapter)
            tools: 사용 가능한 Tool 리스트
            model: 모델명
            max_iterations: 최대 반복 횟수
            verbose: 중간 과정 출력 여부
        """
        self.adapter = adapter
        self.tools = {tool.name: tool for tool in tools}
        self.model = model
        self.max_iterations = max_iterations
        self.verbose = verbose

        # Tool을 API 형식으로 변환
        self.api_tools = adapter.convert_tools_to_api_format(tools)

    def run(self, query: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Agent 실행

        Args:
            query: 사용자 질문/요청
            system_prompt: 시스템 프롬프트 (선택)
            **kwargs: API 추가 파라미터

        Returns:
            최종 응답
        """
        # 메시지 초기화
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": query})

        if self.verbose:
            print(f"[Agent] Query: {query}")
            print(f"[Agent] Available tools: {list(self.tools.keys())}")

        # ReAct Loop
        for iteration in range(self.max_iterations):
            if self.verbose:
                print(f"\n[Agent] Iteration {iteration + 1}/{self.max_iterations}")

            # 1. LLM 호출
            response = self.adapter.call_with_tools(
                messages=messages, tools=self.api_tools, model=self.model, **kwargs
            )

            # 2. Tool Call 확인
            if not self.adapter.has_tool_calls(response):
                # Tool Call이 없으면 최종 응답 반환
                final_content = self.adapter.get_final_content(response)
                if self.verbose:
                    print(f"[Agent] Final answer: {final_content}")
                return final_content

            # 3. Tool Call 추출 및 실행
            tool_calls = self.adapter.extract_tool_calls(response)

            if self.verbose:
                print(f"[Agent] Tool calls: {len(tool_calls)}")

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["arguments"]

                if self.verbose:
                    print(f"[Agent] Calling {tool_name} with args: {tool_args}")

                # Tool 실행
                if tool_name not in self.tools:
                    result = f"Error: Tool '{tool_name}' not found"
                else:
                    try:
                        tool = self.tools[tool_name]
                        result = str(tool.func(**tool_args))
                    except Exception as e:
                        result = f"Error executing {tool_name}: {str(e)}"

                if self.verbose:
                    print(f"[Agent] Result: {result[:100]}...")

                # 결과를 메시지에 추가
                self.adapter.format_tool_result(tool_call, result, messages)

        # 최대 반복 횟수 도달
        raise RuntimeError(
            f"Agent reached maximum iterations ({self.max_iterations}) without completing the task"
        )

    def get_conversation_history(self) -> List[Dict]:
        """
        대화 히스토리 반환 (디버깅용)

        Note: 현재 구현은 stateless이므로 별도로 추적 필요
        """
        # TODO: 대화 히스토리 추적 구현
        pass


class ToolRegistry:
    """
    Tool 레지스트리

    여러 Tool을 관리하고 쉽게 등록/조회할 수 있는 유틸리티
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Tool 등록"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Tool 조회"""
        return self._tools.get(name)

    def list(self) -> List[Tool]:
        """모든 Tool 리스트 반환"""
        return list(self._tools.values())

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
