from openai import OpenAI
from aether.agents.base import Agent
from aether.llm.agent.tools import OpenAIToolCallAdapter
from aether.llm.base import BaseLLM


class StatementAgent(Agent):
    """
    Statement Agent
    """

    def __init__(
        self, model: str, client: OpenAI, system_promt_path: str = "statement.txt"
    ):
        super().__init__(model, client, system_promt_path)
        self.tool_call_adapter = OpenAIToolCallAdapter(model, client)

    def run(self) -> str:
        """
        Statement Development Agent Run
        """
        ...
