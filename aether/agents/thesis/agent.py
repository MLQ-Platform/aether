from openai import OpenAI
from aether.agents.base import Agent
from aether.agents.thesis.schema import Thesis
from aether.clause.tree.base import ClauseTree
from aether.llm.prompt import load_prompt
from aether.llm.structured import StructuredLLM
from aether.logger import get_logger

logger = get_logger(__name__)


class ThesisRevealingAgent(Agent):
    """
    Thesis Revealing Agent
    """

    def __init__(
        self,
        model: str,
        client: OpenAI,
        system_promt_path: str = "thesis-revealing.txt",
        **kwargs,
    ):
        super().__init__(model, client, system_promt_path)
        self.llm = StructuredLLM(model, client, schema=Thesis, **kwargs)

    def run(self, tree_a: ClauseTree, tree_b: ClauseTree) -> Thesis:
        """
        Tree Explain Agent Run
        """

        user_message = self.user_message(tree_a, tree_b)

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

            logger.info(f"Thesis generated ({len(result.thesis)} chars)")

        except Exception as e:
            logger.error(f"Thesis generation failed: {e}")
            return None

        return result

    async def run_async(self, tree_a: ClauseTree, tree_b: ClauseTree) -> Thesis:
        """
        Thesis Revealing Agent Run (async)
        """
        user_message = self.user_message(tree_a, tree_b)
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
            logger.info(f"Thesis generated ({len(result.thesis)} chars)")
        except Exception as e:
            logger.error(f"Thesis generation failed: {e}")
            return None

        return result

    def user_message(self, tree_a: ClauseTree, tree_b: ClauseTree) -> str:
        """
        User Message
        """
        # Build each section precisely with no extra indentation
        tree_a_str = tree_a.render(return_str=True)
        tree_b_str = tree_b.render(return_str=True)
        desc_a = tree_a.get_node_descriptions()
        desc_b = tree_b.get_node_descriptions()
        node_desc_str = f"{desc_a}\n{desc_b}"

        return (
            f"<tree_a>\n{tree_a_str}\n</tree_a>\n\n"
            f"<tree_b>\n{tree_b_str}\n</tree_b>\n\n"
            f"<node_descriptions>\n{node_desc_str}\n</node_descriptions>\n"
        )
