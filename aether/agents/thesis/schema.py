from typing import Optional
from pydantic import BaseModel
from pydantic import Field


class Thesis(BaseModel):
    """
    Thesis
    """

    uuid: Optional[int] = None

    thesis: str = Field(description="Thesis statement")
