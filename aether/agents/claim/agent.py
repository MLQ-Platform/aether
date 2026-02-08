from openai import OpenAI
from aether.agents.base import Agent
from aether.agents.claim.schema import Claim
from aether.agents.claim.schema import ClaimList
from aether.config import DataSchema
from aether.llm.prompt import load_prompt
from aether.llm.structured import StructuredLLM
from aether.logger import get_logger

logger = get_logger(__name__)


class ClaimDecompositionAgent(Agent):
    """
    Claim Decomposition Agent
    """

    def __init__(
        self,
        model: str,
        client: OpenAI,
        system_promt_path: str = "statement-claim.txt",
        **kwargs,
    ):
        super().__init__(model, client, system_promt_path)
        self.llm = StructuredLLM(model, client, schema=ClaimList, **kwargs)

    def run(self, thesis: str) -> ClaimList:
        """
        Claim Decomposition Agent Run
        """

        user_prompt = self.user_message(thesis)

        schema = DataSchema()
        schema_description = schema.get_description(with_index=False)

        system_prompt = load_prompt(
            self.system_promt_path, DATA_DESCRIPTIONS=schema_description
        )

        try:
            result = self.llm.invoke(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ]
            )

            logger.info(f"Claims decomposed ({len(result.claims)} claims)")

        except Exception as e:
            logger.error(f"Claim decomposition failed: {e}")
            return None

        return result

    async def run_async(self, thesis: str) -> ClaimList:
        """
        Claim Decomposition Agent Run (async)
        """
        user_prompt = self.user_message(thesis)

        schema = DataSchema()
        schema_description = schema.get_description(with_index=False)

        system_prompt = load_prompt(
            self.system_promt_path, DATA_DESCRIPTIONS=schema_description
        )

        try:
            result = await self.llm.invoke_async(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ]
            )
            logger.info(f"Claims decomposed ({len(result.claims)} claims)")
        except Exception as e:
            logger.error(f"Claim decomposition failed: {e}")
            return None

        return result

    def user_message(self, thesis: str) -> str:
        """
        User Message
        """
        return f"<thesis>\n{thesis}\n</thesis>\n"


class ClaimModifyAgent(Agent):
    """
    Claim Modify Agent
    """

    def __init__(
        self,
        model: str,
        client: OpenAI,
        system_promt_path: str = "statement-claim-modify.txt",
        **kwargs,
    ):
        super().__init__(model, client, system_promt_path)
        self.llm = StructuredLLM(model, client, schema=Claim, **kwargs)

    async def run_async(self, claim: Claim, rationale: str) -> Claim:
        """
        Claim Modify Agent Run Async
        """
        user_prompt = self.user_message(claim, rationale)

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
                        "content": user_prompt,
                    },
                ]
            )

            logger.info("Claim modified")

        except Exception as e:
            logger.error(f"Claim modification failed: {e}")
            return None

        return result

    def user_message(self, claim: Claim, rationale: str) -> str:
        """
        User Message
        """
        return (
            f"<original_claim>\n"
            f"<claim>{claim.claim}</claim>\n"
            f"<condition>{claim.condition}</condition>\n"
            f"<data_columns>{claim.data_columns}</data_columns>\n"
            f"<verification_plan>{claim.verification_plan}</verification_plan>\n"
            f"</original_claim>\n\n"
            f"<rationale>\n"
            f"<content>{rationale}</content>\n"
            f"</rationale>\n"
        )
