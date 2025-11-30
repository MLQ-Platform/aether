from openai import OpenAI
from aether.agents.base import Agent
from aether.agents.claim.schema import ClaimList
from aether.config import DataSchema
from aether.llm.prompt import load_prompt
from aether.llm.structured import StructuredLLM


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

        except Exception as e:
            print(f"LLM Invoke Error: {e}")
            return None

        return result

    def user_message(self, thesis: str) -> str:
        """
        User Message
        """
        return f"<thesis>\n{thesis}\n</thesis>\n"
