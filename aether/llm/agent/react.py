import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List
from typing import Optional
from aether.llm.agent.tools.adapter import ToolCallAdapter
from aether.llm.agent.tools.base import Tool


class ReactAgent:
    """
    ReAct Agent
    """

    # Shared ThreadPoolExecutor for all instances
    _shared_executor: Optional[ThreadPoolExecutor] = None

    def __init__(
        self,
        adapter: ToolCallAdapter,
        tools: List[Tool],
        max_iterations: int = 10,
        verbose: bool = False,
    ):
        self.adapter = adapter
        self.tools = {tool.name: tool for tool in tools}
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
            print(f"[Agent] Available tools: {list(self.tools.keys())}")

        # ReAct Loop
        for iteration in range(self.max_iterations):
            if self.verbose:
                print(f"\n[Agent] Iteration {iteration + 1}/{self.max_iterations}")

            # 1. LLM 호출
            print("[Agent] Start LLM API Calling")
            response = self.adapter.call_with_tools(
                messages=messages, tools=self.api_tools, **kwargs
            )

            # 2. Tool Call 확인
            if not self.adapter.has_tool_calls(response):
                # Tool Call이 없으면 최종 응답 반환
                final_content = self.adapter.get_final_content(response)
                return final_content

            # 3. Tool Call 추출 및 실행
            tool_calls = self.adapter.extract_tool_calls(response)
            # Tool call 시 LLM의 추론 과정(content) 확인 및 출력
            reasoning = self.adapter.get_final_content(response)

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["arguments"]

                if self.verbose:
                    print(f"[Agent] Start Calling: {tool_name}")

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

                # 결과를 메시지에 추가 (reasoning 포함)
                self.adapter.format_tool_result(tool_call, result, messages, reasoning)

        # 최대 반복 횟수 도달 - 최종 답변 강제 요청
        if self.verbose:
            print("\n[Agent] Max iterations reached. Requesting final answer...")

        # 최종 답변 요청 메시지 추가
        messages.append(
            {
                "role": "user",
                "content": "You have reached the maximum number of tool calls. Please provide your final answer based on the information gathered so far.",
            }
        )

        # Tool 없이 최종 답변 요청
        final_response = self.adapter.call_with_tools(
            messages=messages, tools=[], **kwargs
        )
        final_content = self.adapter.get_final_content(final_response)

        print("[Agent] Final Done")
        return final_content

    async def run_async(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        exec_context: Optional[dict] = {},
        **kwargs,
    ) -> str:
        """
        Async Agent 실행

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
            print(f"[Agent] Available tools: {list(self.tools.keys())}")

        # Use shared ThreadPoolExecutor (lazy initialization)
        if ReactAgent._shared_executor is None:
            ReactAgent._shared_executor = ThreadPoolExecutor(max_workers=1)

        executor = ReactAgent._shared_executor
        loop = asyncio.get_event_loop()

        # Timeout for tool execution (30 seconds)
        TOOL_TIMEOUT = 30

        # ReAct Loop
        for iteration in range(self.max_iterations):
            if self.verbose:
                print(f"\n[Agent] Iteration {iteration + 1}/{self.max_iterations}")

            print("[Agent] Start LLM API Calling")
            # 1. LLM 호출 (async)
            response = await self.adapter.call_with_tools(
                messages=messages, tools=self.api_tools, **kwargs
            )

            # 2. Tool Call 확인
            if not self.adapter.has_tool_calls(response):
                # Tool Call이 없으면 최종 응답 반환
                final_content = self.adapter.get_final_content(response)
                # Don't shutdown shared executor
                return final_content

            # 3. Tool Call 추출 및 실행
            tool_calls = self.adapter.extract_tool_calls(response)
            # Tool call 시 LLM의 추론 과정(content) 확인 및 출력
            reasoning = self.adapter.get_final_content(response)

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["arguments"]

                if self.verbose:
                    print(f"[Agent] Start Calling: {tool_name}")

                # Tool 실행
                if tool_name not in self.tools:
                    result = f"Error: Tool '{tool_name}' not found"
                else:
                    try:
                        tool = self.tools[tool_name]

                        def run_tool():
                            # All tools accept exec_context and return (result, exec_context) tuple
                            tool_result = tool.func(
                                **tool_args, exec_context=exec_context
                            )
                            return tool_result

                        # 별도 쓰레드에서 실행
                        tool_result = await asyncio.wait_for(
                            loop.run_in_executor(executor, run_tool),
                            timeout=TOOL_TIMEOUT,
                        )

                        result, exec_context = tool_result
                        result = str(result)

                    except asyncio.TimeoutError:
                        result = f"Error: Tool '{tool_name}' execution exceeded {TOOL_TIMEOUT} seconds timeout."
                        # Keep exec_context unchanged on timeout

                    except Exception as e:
                        result = f"Error executing {tool_name}: {str(e)}"
                        # Keep exec_context unchanged on error

                if self.verbose:
                    print(f"[Agent] Result: {result[:100]}...")

                # 결과를 메시지에 추가 (reasoning 포함)
                self.adapter.format_tool_result(tool_call, result, messages, reasoning)

        # 최대 반복 횟수 도달 - 최종 답변 강제 요청
        if self.verbose:
            print("\n[Agent] Max iterations reached. Requesting final answer...")

        # 최종 답변 요청 메시지 추가
        messages.append(
            {
                "role": "user",
                "content": "You have reached the maximum number of tool calls. Please provide your final answer based on the information gathered so far.",
            }
        )

        # Tool 없이 최종 답변 요청 (async)
        final_response = await self.adapter.call_with_tools(
            messages=messages, tools=[], **kwargs
        )
        final_content = self.adapter.get_final_content(final_response)

        print("[Agent] Final Done")
        return final_content
