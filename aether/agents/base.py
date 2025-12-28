from typing import Any
from openai import OpenAI


class Agent:
    """
    Base Agent class
    """

    def __init__(self, model: str, client: OpenAI, system_promt_path: str):
        self.model = model
        self.client = client
        self.system_promt_path = system_promt_path

    def run(self, **kwargs) -> Any:
        raise NotImplementedError("Subclasses must implement this method")

    def load_prompt(self, **kwargs) -> str:
        raise NotImplementedError("Subclasses must implement this method")
