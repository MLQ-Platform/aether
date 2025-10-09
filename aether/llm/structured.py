import json
import re
from typing import Optional
from typing import TypeVar
from openai import OpenAI
from pydantic import BaseModel
from pydantic import ValidationError
from aether.llm.types import Messages

T = TypeVar("T", bound=BaseModel)


class StructuredLLM:
    """
    Structured Output을 생성하는 LLM

    Example:
        from pydantic import BaseModel

        class Answer(BaseModel):
            text: str
            confidence: float

        structured_llm = StructuredLLM(client, schema=Answer)

        # 기본 사용
        result = structured_llm.invoke([
            {"role": "user", "content": "What is 2+2?"}
        ])

        # 커스텀 시스템 프롬프트
        result = structured_llm.invoke([
            {"role": "system", "content": "You are a math expert"},
            {"role": "user", "content": "What is 2+2?"}
        ])
    """

    def __init__(
        self,
        model: str,
        client: OpenAI,
        schema: type[BaseModel],
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        max_retries: int = 3,
        **kwargs,
    ):
        """
        Args:
            client: OpenAI 클라이언트 (OpenAI 호환 API 모두 가능)
            schema: Pydantic 모델 클래스
            model: 모델명
            temperature: 생성 온도
            max_tokens: 최대 토큰 수
            max_retries: 최대 재시도 횟수
            **kwargs: 추가 파라미터
        """

        self.client = client
        self.schema = schema
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.default_params = kwargs

    def __repr__(self) -> str:
        return f"StructuredLLM(schema={self.schema.__name__}, model={self.model})"

    def invoke(self, messages: Messages, **kwargs) -> BaseModel:
        """
        구조화된 출력 생성

        Args:
            messages: 메시지 리스트 (시스템 메시지 포함 가능)
            **kwargs: 추가 파라미터

        Returns:
            검증된 Pydantic 모델 인스턴스
        """
        params = self._prepare_params(kwargs)
        json_schema = self.schema.model_json_schema()

        # JSON 스키마 지시사항
        json_instruction = (
            "You must respond with ONLY valid JSON. "
            "Do NOT include any markdown formatting, code blocks, or explanations. "
            "Output ONLY the raw JSON object.\n\n"
            f"Required JSON Schema:\n{json.dumps(json_schema, indent=2)}"
        )

        # 메시지 처리: 기존 시스템 메시지가 있으면 병합, 없으면 새로 생성
        full_messages = self._prepare_messages(messages, json_instruction)

        for attempt in range(self.max_retries):
            try:
                # response_format은 선택적으로 사용 (일부 모델은 지원 안 함)
                create_params = {
                    "model": self.model,
                    "messages": full_messages,
                    **params,
                }

                completion = self.client.chat.completions.create(**create_params)
                content = completion.choices[0].message.content

                # 마크다운 코드 블록 제거
                json_string = self._extract_json(content)
                data = json.loads(json_string)
                return self.schema(**data)

            except (json.JSONDecodeError, ValidationError) as e:
                if attempt < self.max_retries - 1:
                    full_messages.append({"role": "assistant", "content": content})
                    full_messages.append(
                        {
                            "role": "user",
                            "content": f"Invalid response. Error: {str(e)}\nPlease respond with valid JSON matching the schema.",
                        }
                    )
                else:
                    raise ValueError(
                        f"Failed to generate valid structured output after {self.max_retries} attempts.\n"
                        f"Last error: {e}\n"
                        f"Last response: {content[:200]}..."
                    )

        raise RuntimeError("Unexpected error in invoke")

    def _extract_json(self, text: str) -> str:
        """
        마크다운 코드 블록에서 JSON 추출
        """
        # ```json ... ``` 또는 ``` ... ``` 패턴 찾기
        pattern = r"```(?:json)?\s*(.*?)\s*```"
        matches = re.findall(pattern, text, re.DOTALL)

        if matches:
            return matches[0].strip()

        # 코드 블록이 없으면 그대로 반환
        return text.strip()

    def _prepare_messages(self, messages: Messages, json_instruction: str) -> Messages:
        """
        메시지 준비: 시스템 메시지 처리
        """
        # 첫 번째 메시지가 시스템 메시지인지 확인
        if messages and messages[0].get("role") == "system":
            # 기존 시스템 메시지에 JSON 지시사항 추가
            user_system_content = messages[0]["content"]
            combined_system = {
                "role": "system",
                "content": f"{user_system_content}\n\n{json_instruction}",
            }
            return [combined_system] + messages[1:]
        else:
            # 시스템 메시지가 없으면 JSON 지시사항만으로 생성
            system_msg = {"role": "system", "content": json_instruction}
            return [system_msg] + messages

    def _prepare_params(self, override_params: dict) -> dict:
        """
        파라미터 준비
        """
        params = {**self.default_params, **override_params}

        if self.temperature is not None:
            params.setdefault("temperature", self.temperature)

        if self.max_tokens is not None:
            params.setdefault("max_tokens", self.max_tokens)

        return params
