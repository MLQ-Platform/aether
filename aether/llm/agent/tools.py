import json
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from openai import OpenAI
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


class ToolCallAdapter(ABC):
    """
    모델별 Tool Calling 어댑터 추상 클래스

    각 LLM 제공자(OpenAI, Anthropic, Google 등)의
    Tool Calling 형식 차이를 추상화합니다.
    """

    @abstractmethod
    def convert_tools_to_api_format(self, tools: List[Tool]) -> List[Dict]:
        """Tool 리스트를 해당 모델의 API 형식으로 변환"""
        pass

    @abstractmethod
    def call_with_tools(
        self, messages: List[Dict], tools: List[Dict], model: str, **kwargs
    ) -> Any:
        """Tool을 사용한 API 호출"""
        pass

    @abstractmethod
    def extract_tool_calls(self, response: Any) -> List[Dict]:
        """응답에서 Tool Call 추출"""
        pass

    @abstractmethod
    def has_tool_calls(self, response: Any) -> bool:
        """응답에 Tool Call이 있는지 확인"""
        pass

    @abstractmethod
    def format_tool_result(
        self, tool_call: Dict, result: str, messages: List[Dict]
    ) -> None:
        """Tool 실행 결과를 메시지에 추가 (in-place)"""
        pass

    @abstractmethod
    def get_final_content(self, response: Any) -> str:
        """최종 응답 텍스트 추출"""
        pass


class OpenAIToolCallAdapter(ToolCallAdapter):
    """
    OpenAI Tool Calling 어댑터

    OpenAI 및 OpenAI 호환 API (OpenRouter 등)에서 사용
    """

    def __init__(self, client: OpenAI):
        self.client = client

    def convert_tools_to_api_format(self, tools: List[Tool]) -> List[Dict]:
        """Tool → OpenAI tools 형식"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in tools
        ]

    def call_with_tools(
        self, messages: List[Dict], tools: List[Dict], model: str, **kwargs
    ) -> Any:
        """OpenAI API 호출"""
        return self.client.chat.completions.create(
            model=model, messages=messages, tools=tools, **kwargs
        )

    def extract_tool_calls(self, response: Any) -> List[Dict]:
        """OpenAI 응답에서 tool calls 추출"""
        message = response.choices[0].message

        if not message.tool_calls:
            return []

        return [
            {
                "id": tc.id,
                "name": tc.function.name,
                "arguments": json.loads(tc.function.arguments),
            }
            for tc in message.tool_calls
        ]

    def has_tool_calls(self, response: Any) -> bool:
        """Tool Call이 있는지 확인"""
        message = response.choices[0].message
        return bool(message.tool_calls)

    def format_tool_result(
        self, tool_call: Dict, result: str, messages: List[Dict]
    ) -> None:
        """Tool 결과를 메시지에 추가 (OpenAI 형식)"""
        # Assistant의 tool call 추가
        messages.append(
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tool_call["id"],
                        "type": "function",
                        "function": {
                            "name": tool_call["name"],
                            "arguments": json.dumps(tool_call["arguments"]),
                        },
                    }
                ],
            }
        )

        # Tool 실행 결과 추가
        messages.append(
            {"role": "tool", "tool_call_id": tool_call["id"], "content": result}
        )

    def get_final_content(self, response: Any) -> str:
        """최종 응답 텍스트 추출"""
        return response.choices[0].message.content or ""
