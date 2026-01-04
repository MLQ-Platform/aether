from typing import Optional
from pydantic import BaseModel
from pydantic import Field


class Claim(BaseModel):
    """
    Thesis로부터 분해된 최소 논리 단위
    """

    uuid: Optional[int] = None

    claim: str = Field(
        description="A verifiable proposition sentence (must be atomic and specific)"
    )

    condition: str = Field(
        description=(
            "Mathematical/statistical condition expression using data columns, operators, and numerical thresholds."
            "Examples: 'skew(OPEN, window=20) > 0'"
        )
    )

    data_columns: list[str] = Field(
        description="List of data column names required to verify this claim (e.g., ['CLOSE', 'VOLUME'])"
    )

    verification_plan: str = Field(
        description=(
            "Data-driven verification strategy describing how to empirically test this claim."
        )
    )


class ClaimList(BaseModel):
    """
    Thesis로부터 분해된 Claim들의 리스트
    """

    claims: list[Claim] = Field(description="Decomposed claim list")
