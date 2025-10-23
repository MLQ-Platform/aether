import json
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List
from openai import OpenAI
from aether.llm.agent.tools.base import Tool


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
        self, tool_call: Dict, result: str, messages: List[Dict], reasoning: str = None
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

    def __init__(self, model: str, client: OpenAI):
        self.model = model
        self.client = client

    def convert_tools_to_api_format(self, tools: List[Tool]) -> List[Dict]:
        """
        Tool → OpenAI tools 형식
        """
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

    def call_with_tools(self, messages: List[Dict], tools: List[Dict], **kwargs) -> Any:
        """
        OpenAI API 호출
        """
        # parallel_tool_calls를 명시적으로 설정하지 않으면 기본값 사용
        # False로 설정하면 한 번에 하나씩만 호출 (reasoning이 더 자세해질 수 있음)
        return self.client.chat.completions.create(
            model=self.model, messages=messages, tools=tools, **kwargs
        )

    def extract_tool_calls(self, response: Any) -> List[Dict]:
        """
        OpenAI 응답에서 tool calls 추출
        """
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
        """
        Tool Call이 있는지 확인
        """
        message = response.choices[0].message
        return bool(message.tool_calls)

    def format_tool_result(
        self, tool_call: Dict, result: str, messages: List[Dict], reasoning: str = None
    ) -> None:
        """
        Tool 결과를 메시지에 추가 (OpenAI 형식)

        Args:
            tool_call: Tool 호출 정보
            result: Tool 실행 결과
            messages: 메시지 리스트
            reasoning: LLM의 추론 과정 텍스트 (선택)
        """
        # Assistant의 tool call 추가 (reasoning도 포함)
        messages.append(
            {
                "role": "assistant",
                "content": reasoning if reasoning else None,
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
        """
        최종 응답 텍스트 추출
        """
        return response.choices[0].message.content or ""
