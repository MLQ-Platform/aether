from openai import OpenAI
from aether.agents.base import Agent
from aether.agents.factor.schema import FactorCode
from aether.agents.factor.schema import FactorStatement
from aether.agents.factor.schema import ProofRevision
from aether.config import DataSchema
from aether.llm.prompt import load_prompt
from aether.llm.structured import StructuredLLM
from aether.logger import get_logger

logger = get_logger(__name__)


class InitialFactorStatementAgent(Agent):
    """
    Initial Factor Statement Agent
    """

    def __init__(
        self,
        model: str,
        client: OpenAI,
        system_promt_path: str = "agent-factor-initial.txt",
        **kwargs,
    ):
        super().__init__(model, client, system_promt_path)
        self.llm = StructuredLLM(model, client, schema=FactorStatement, **kwargs)

    def run(self, market_statement: str) -> FactorStatement:
        """
        Initial Factor Statement Agent Run
        """

        user_prompt = self.user_message(market_statement)
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
                        "content": user_prompt,
                    },
                ]
            )

            logger.info("Initial factor statement generated")

        except Exception as e:
            logger.error(f"Initial factor generation failed: {e}")
            return None

        return result

    def user_message(self, market_statement: str) -> str:
        """
        User Message
        """
        return f"<market_statement>\n{market_statement}\n</market_statement>\n"


class ProofCheckAgent(Agent):
    """
    Proof Check Agent
    """

    def __init__(
        self,
        model: str,
        client: OpenAI,
        system_promt_path: str = "agent-factor-check.txt",
        **kwargs,
    ):
        super().__init__(model, client, system_promt_path)
        self.llm = StructuredLLM(model, client, schema=ProofRevision, **kwargs)

    def run(self, proof: str) -> ProofRevision:
        """
        Initial Factor Statement Agent Run
        """

        user_prompt = self.user_message(proof)
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
                        "content": user_prompt,
                    },
                ]
            )

            logger.info("Proof check completed")

        except Exception as e:
            logger.error(f"Proof check failed: {e}")
            return None

        return result

    def user_message(self, proof: str) -> str:
        """
        User Message
        """
        return f"<proof>\n{proof}\n</proof>\n"


class ProofFixAgent(Agent):
    """
    Proof Fix Agent
    """

    def __init__(
        self,
        model: str,
        client: OpenAI,
        system_promt_path: str = "agent-factor-fix.txt",
        **kwargs,
    ):
        super().__init__(model, client, system_promt_path)
        self.llm = StructuredLLM(model, client, schema=FactorStatement, **kwargs)

    def run(self, proof: str, revisions: ProofRevision) -> FactorStatement:
        """
        Initial Factor Statement Agent Run
        """

        user_prompt = self.user_message(proof, revisions)
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
                        "content": user_prompt,
                    },
                ]
            )

            logger.info("Proof fix applied")

        except Exception as e:
            logger.error(f"Proof fix failed: {e}")
            return None

        return result

    def user_message(self, proof: str, revisions: ProofRevision) -> str:
        """
        User Message
        """
        return (
            f"<proof>\n{proof}\n</proof>\n\n"
            f"<revisions>\n{revisions.revision}\n</revisions>\n"
        )


class FactorCodeAgent(Agent):
    """
    Factor Code Agent
    """

    def __init__(
        self,
        model: str,
        client: OpenAI,
        system_promt_path: str = "agent-factor-code.txt",
        **kwargs,
    ):
        super().__init__(model, client, system_promt_path)
        self.llm = StructuredLLM(model, client, schema=FactorCode, **kwargs)

    def run(self, proof: str) -> FactorCode:
        """
        Initial Factor Statement Agent Run
        """

        user_prompt = self.user_message(proof)

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

            logger.info("Factor code generated")

        except Exception as e:
            logger.error(f"Factor code generation failed: {e}")
            return None

        return result

    def user_message(self, proof: str) -> str:
        """
        User Message
        """
        return f"<proof>\n{proof}\n</proof>\n"
