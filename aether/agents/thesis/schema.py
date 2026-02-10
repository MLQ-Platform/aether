from pydantic import BaseModel
from pydantic import Field


class Thesis(BaseModel):
    """
    Thesis
    """

    uuid: int | None = None

    thesis: str = Field(description="Thesis statement")
