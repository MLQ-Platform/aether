from pydantic import BaseModel
from pydantic import Field


class LogicalChain(BaseModel):
    chains: list[str] = Field(description="The logical chain of propositions")
