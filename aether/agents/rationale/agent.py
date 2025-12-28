from typing import List
from typing import Union
from openai import AsyncOpenAI
from openai import OpenAI
from aether.agents.base import Agent
from aether.agents.claim.schema import Claim
from aether.agents.rationale.schema import Rationale
from aether.config import DataSchema
from aether.llm.agent import AsyncOpenAIToolCallAdapter
from aether.llm.agent import ReactAgent
from aether.llm.agent import Tool
from aether.llm.prompt import load_prompt
from aether.llm.structured import StructuredLLM


class RationaleAgent(Agent):
    """
    Rationale Generation Agent
    """

    def __init__(
        self,
        model: str,
        client: Union[OpenAI, AsyncOpenAI],
        tools: List[Tool],
        system_promt_path: str = "statement-rationale.txt",
        **kwargs,
    ):
        super().__init__(model, client, system_promt_path)

        self.client = client
        self.adapter = AsyncOpenAIToolCallAdapter(model, client)
        # code execution agent
        self.agent = ReactAgent(self.adapter, tools, **kwargs)
        # structured llm
        self.structured_llm = StructuredLLM(model, client, schema=Rationale)

    async def run_async(
        self, claim: Claim, exec_context: dict = {}
    ) -> Union[str, Rationale]:
        """
        Async Rationale Generation Agent Run
        """
        schema = DataSchema()
        schema_description = schema.get_description(with_index=True)

        # User Message
        user_message = self.user_message(claim)
        # Load System Prompt
        system_prompt = load_prompt(
            self.system_promt_path, DATA_SCHEMA=schema_description
        )

        try:
            result = await self.agent.run_async(
                query=user_message,
                system_prompt=system_prompt,
                exec_context=exec_context,
            )

            result = await self.to_schema_async(result)

        except Exception as e:
            print(f"LLM Invoke Error: {e}")
            return None

        return result

    async def to_schema_async(self, rationale: str) -> Rationale:
        """
        Async Answer to Rationale Schema
        """

        result = await self.structured_llm.invoke_async(
            messages=[
                {
                    "role": "user",
                    "content": rationale,
                }
            ]
        )
        return result

    def user_message(self, claim: Claim) -> str:
        """
        User Message
        """
        return (
            f"<claim>\n"
            f"<claim>{claim.claim}</claim>\n"
            f"<data_columns>{claim.data_columns}</data_columns>\n"
            f"<verification_plan>{claim.verification_plan}</verification_plan>\n"
            f"</claim>\n"
        )

    def to_schema(self, rationale: str) -> Rationale:
        """
        Answer to Rationale Schema
        """

        result = self.structured_llm.invoke(
            messages=[
                {
                    "role": "user",
                    "content": rationale,
                }
            ]
        )
        return result
