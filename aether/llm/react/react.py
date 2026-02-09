import asyncio
import atexit
from concurrent.futures import ThreadPoolExecutor
from typing import List
from typing import Optional
from aether.llm.react.tools.adapter import ToolCallAdapter
from aether.llm.react.tools.base import Tool
from aether.logger import get_logger
from aether.utils import generate_task_id

logger = get_logger(__name__)


class ReactAgent:
    """
    ReAct Agent
    """

    # Shared ThreadPoolExecutor for all instances
    _shared_executor: Optional[ThreadPoolExecutor] = None
    _shutdown_registered = False

    def __init__(
        self,
        adapter: ToolCallAdapter,
        tools: List[Tool],
        max_iterations: int = 10,
    ):
        self.adapter = adapter
        self.tools = {tool.name: tool for tool in tools}
        self.max_iterations = max_iterations

        # Tool을 API 형식으로 변환
        self.api_tools = adapter.convert_tools_to_api_format(tools)

    def run(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        task_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Agent 실행
        """
        task_id = task_id or generate_task_id()

        # 메시지 초기화
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": query})

        # ReAct Loop
        for iteration in range(self.max_iterations):
            logger.debug(
                f"[Task {task_id}] Iteration {iteration + 1}/{self.max_iterations}"
            )

            # 1. LLM Tool Calling 호출
            response = self.adapter.call_with_tools(
                messages=messages,
                tools=self.api_tools,
                tool_choice="required",
                **kwargs,
            )

            # 2. Tool Call 확인 (비정상 케이스)
            if not self.adapter.has_tool_calls(response):
                logger.warning(f"[Task {task_id}] No tool call")
                continue

            # 3. Tool Call 추출 및 실행
            tool_calls = self.adapter.extract_tool_calls(response)
            # Tool call 시 LLM의 추론 과정(content) 확인 및 출력
            reasoning = self.adapter.get_final_content(response)
            logger.debug(
                f"[Task {task_id}] Reasoning: {reasoning}",
            )
            logger.debug(f"[Task {task_id}] Executing {len(tool_calls)} tools")

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["arguments"]

                try:
                    tool = self.tools[tool_name]
                    result = str(tool.func(**tool_args))
                    logger.debug(f"[Task {task_id}] Tool {tool_name} completed")

                except Exception as e:
                    result = f"Error executing tool {tool_name}: {str(e)}"
                    logger.warning(
                        f"[Task {task_id}] Tool {tool_name} failed: {str(e)}"
                    )

                # 결과를 메시지에 추가 (reasoning 포함)
                self.adapter.format_tool_result(tool_call, result, messages, reasoning)

        # 최종 답변 요청 메시지 추가
        messages.append(
            {
                "role": "user",
                "content": "Provide your final answer based on the information gathered so far.",
            }
        )

        # 최종 답변 요청
        final_response = self.adapter.call_with_tools(
            messages=messages,
            tools=[],
            tool_choice="none",
            **kwargs,
        )
        final_content = self.adapter.get_final_content(final_response)

        logger.info(f"[Task {task_id}] Agent completed")
        return final_content

    async def run_async(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        exec_context: Optional[dict] = {},
        task_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Async Agent 실행
        """
        TOOL_TIMEOUT = 180

        task_id = task_id or generate_task_id()

        # 메시지 초기화
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": query})

        # Use shared ThreadPoolExecutor (lazy initialization)
        if ReactAgent._shared_executor is None:
            ReactAgent._shared_executor = ThreadPoolExecutor(max_workers=1)
            ReactAgent._ensure_shutdown_registered()

        executor = ReactAgent._shared_executor
        loop = asyncio.get_event_loop()

        # ReAct Loop
        for iteration in range(self.max_iterations):
            logger.debug(
                f"[Task {task_id}] Iteration {iteration + 1}/{self.max_iterations}"
            )

            # 1. LLM Tool Calling 호출 (async)
            response = await self.adapter.call_with_tools(
                messages=messages,
                tools=self.api_tools,
                tool_choice="required",
                **kwargs,
            )

            # 2. Tool Call 확인 (비정상 케이스)
            if not self.adapter.has_tool_calls(response):
                logger.warning(f"[Task {task_id}] No tool call")
                continue

            # 3. Tool Call 추출 및 실행
            tool_calls = self.adapter.extract_tool_calls(response)
            # Tool call 시 LLM의 추론 과정(content) 확인 및 출력
            reasoning = self.adapter.get_final_content(response)

            logger.debug(
                f"[Task {task_id}] Reasoning: {reasoning}",
            )
            logger.debug(f"[Task {task_id}] Executing {len(tool_calls)} tools")

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["arguments"]

                try:
                    tool = self.tools[tool_name]

                    def run_tool():
                        # All tools accept exec_context and return (result, exec_context) tuple
                        tool_result = tool.func(**tool_args, exec_context=exec_context)
                        return tool_result

                    # 별도 쓰레드에서 실행
                    tool_result = await asyncio.wait_for(
                        loop.run_in_executor(executor, run_tool),
                        timeout=TOOL_TIMEOUT,
                    )

                    result, exec_context = tool_result
                    result = str(result)
                    logger.debug(f"[Task {task_id}] Tool {tool_name} completed")

                except asyncio.TimeoutError:
                    result = f"Error: Tool '{tool_name}' execution exceeded {TOOL_TIMEOUT} seconds timeout."
                    logger.error(
                        f"[Task {task_id}] Tool {tool_name} timed out after {TOOL_TIMEOUT}s"
                    )
                except Exception as e:
                    result = f"Error executing tool {tool_name}: {str(e)}"
                    logger.warning(
                        f"[Task {task_id}] Tool {tool_name} failed: {str(e)}"
                    )

                # 결과를 메시지에 추가 (reasoning 포함)
                self.adapter.format_tool_result(tool_call, result, messages, reasoning)

        # 최종 답변 요청 메시지 추가
        messages.append(
            {
                "role": "user",
                "content": "Provide your final answer based on the information gathered so far.",
            }
        )

        # 최종 답변 요청 (async)
        final_response = await self.adapter.call_with_tools(
            messages=messages,
            tools=[],
            tool_choice="none",
            **kwargs,
        )
        final_content = self.adapter.get_final_content(final_response)

        logger.info(f"[Task {task_id}] Agent completed (iter: {iteration + 1})")
        return final_content

    @classmethod
    def shutdown(cls):
        cls._shutdown_executor(wait=True)

    @classmethod
    def _shutdown_executor(cls, wait: bool = True):
        if cls._shared_executor is not None:
            try:
                # 쓰레드가 완료될 때까지 기다리면서 정리
                cls._shared_executor.shutdown(wait=wait)
                logger.debug("ThreadPoolExecutor shutdown completed")
            except Exception as e:
                logger.warning(f"Error during executor shutdown: {e}")
            finally:
                cls._shared_executor = None

    @classmethod
    def _ensure_shutdown_registered(cls):
        if not cls._shutdown_registered:
            atexit.register(cls._shutdown_executor)
            cls._shutdown_registered = True
