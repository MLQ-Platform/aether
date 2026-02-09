from typing import List
from openai import OpenAI
from aether.agents.base import Agent
from aether.agents.claim.schema import Claim
from aether.agents.statement.schema import Statement
from aether.llm.prompt import load_prompt
from aether.llm.structured import StructuredLLM
from aether.exceptions import AgentExecutionError
from aether.logger import get_logger

logger = get_logger(__name__)


class StatementAgent(Agent):
    """
    Statement Agent
    """

    def __init__(
        self,
        model: str,
        client: OpenAI,
        system_promt_path: str = "statement-final.txt",
        **kwargs,
    ):
        super().__init__(model, client, system_promt_path)
        self.llm = StructuredLLM(model, client, schema=Statement, **kwargs)

    def run(self, claims: List[Claim]) -> str:
        """
        Statement Agent Run
        """

        user_message = self.user_message(claims)

        # Load System Prompt
        system_prompt = load_prompt(self.system_promt_path)

        try:
            result = self.llm.invoke(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_message,
                    },
                ]
            )

            logger.info(f"Statement generated ({len(result.statement)} chars)")

        except Exception as e:
            raise AgentExecutionError("Statement generation failed") from e

        return result

    async def run_async(self, claims: List[Claim]) -> str:
        """
        Statement Agent Run (async)
        """
        user_message = self.user_message(claims)
        system_prompt = load_prompt(self.system_promt_path)

        try:
            result = await self.llm.invoke_async(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_message,
                    },
                ]
            )
            logger.info(f"Statement generated ({len(result.statement)} chars)")
        except Exception as e:
            raise AgentExecutionError("Statement generation failed") from e

        return result

    def user_message(self, claims: List[Claim]) -> str:
        """
        User Message
        """
        # Build each section precisely with no extra indentation
        claims = "\n".join(f"- {claim}" for claim in claims)
        return f"<claims>\n{claims}\n</claims>\n"
