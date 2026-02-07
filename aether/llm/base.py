from typing import Any
from typing import Dict
from typing import Optional
from openai import OpenAI
from aether.llm.types import Messages


class BaseLLM:
    """
    Base LLM 클래스

    LangGraph의 ChatOpenAI와 유사한 인터페이스 제공

    사용법:
        llm = BaseLLM(client, model="gpt-4o-mini")

        # 단일 호출
        response = llm.invoke([{"role": "user", "content": "Hello"}])

        # 파라미터 바인딩
        bound_llm = llm.bind(temperature=0.8, max_tokens=1000)
        response = bound_llm.invoke(messages)
    """

    def __init__(
        self,
        model: str,
        client: OpenAI,
        temperature: float = 0.9,
        max_tokens: Optional[int] = None,
        **kwargs,
    ):
        """
        Args:
            client: OpenAI 클라이언트
            model: 모델명
            temperature: 생성 온도 (0.0-2.0)
            max_tokens: 최대 토큰 수
            **kwargs: 추가 파라미터 (top_p, frequency_penalty 등)
        """
        self.client = client
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.default_params = kwargs

    def __repr__(self) -> str:
        return f"BaseLLM(model={self.model}, temperature={self.temperature})"

    def invoke(self, messages: Messages, **kwargs) -> str:
        """
        LLM 단일 호출
        """
        params = self._prepare_params(kwargs)

        completion = self.client.chat.completions.create(
            model=self.model, messages=messages, **params
        )

        return completion.choices[0].message.content

    def _prepare_params(self, override_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        파라미터 준비
        """
        params = {**self.default_params, **override_params}

        # 기본 파라미터 설정
        if self.temperature is not None:
            params.setdefault("temperature", self.temperature)

        if self.max_tokens is not None:
            params.setdefault("max_tokens", self.max_tokens)

        return params
