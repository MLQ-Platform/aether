from pydantic import BaseModel
from pydantic import Field


class Rationale(BaseModel):
    """
    Rationale
    """

    uuid: int | None = None

    is_accepted: bool = Field(description="Whether this rationale is accepted")

    rationale: str = Field(
        description="A verifiable proposition sentence (must be atomic and specific)"
    )
