from openai import OpenAI
from aether.agents.base import Agent
from aether.clause.tree.base import ClauseTree
from aether.llm.base import BaseLLM
from aether.llm.prompt import load_prompt


class TreeExplainAgent(Agent):
    """
    Tree Explain Agent
    """

    def __init__(
        self, model: str, client: OpenAI, system_promt_path: str = "tree-explain.txt"
    ):
        super().__init__(model, client, system_promt_path)
        self.llm = BaseLLM(model, client)

    def run(self, tree: ClauseTree) -> str:
        """
        Tree Explain Agent Run
        """

        user_message = self.user_message(tree)

        # Load System Prompt
        system_prompt = load_prompt(
            self.system_promt_path,
            tree_structure=tree.render(return_str=True),
            node_descriptions=tree.get_node_descriptions(),
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
                        "content": user_message,
                    },
                ]
            )

        except Exception as e:
            print(f"LLM Invoke Error: {e}")
            return None

        return result

    def user_message(self, tree: ClauseTree) -> str:
        """
        User Message
        """
        return f"""# Your Task
        Tree Structure:
        {tree.render(return_str=True)}

        Node Descriptions:
        {tree.get_node_descriptions()}"""
