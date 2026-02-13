from pydantic import BaseModel
from pydantic import Field


class Thesis(BaseModel):
    """
    Thesis
    """

    thesis: str = Field(description="Thesis statement")
