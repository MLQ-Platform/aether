from typing import Optional
from pydantic import BaseModel
from pydantic import Field


class Statement(BaseModel):
    """
    Statement composed from verified claims
    """

    uuid: Optional[int] = None

    statement: str = Field(
        description="Synthesized statement that logically combines all verified claims without information loss"
    )
