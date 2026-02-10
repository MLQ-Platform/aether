from pydantic import BaseModel
from pydantic import Field


class FactorStatement(BaseModel):
    """
    Factor Statement
    """

    uuid: int | None = None

    conclusion: str = Field(
        description="The concrete final mathematical proposition established through the proof.",
    )

    factor: str = Field(
        description="The concrete mathematical expression of the factor used in the statement, including definitions of all variables, operators, and hyperparameters.",
    )

    proof: str = Field(
        description="The rigorous, step-by-step algebraic full proof of the factor statement, including all assumptions, lemmas, reverse design process, and justifications for each step. Every line should be a mathematical transformation with a justification annotation, showing the connection from lemmas to the final statement.",
    )


class ProofRevision(BaseModel):
    """
    Proof Revision
    """

    revision: str = Field(
        description="The revision items of the factor statement proof in bullet point format.",
    )

    is_pass: bool = Field(
        description="PASS only if the proof has minimal or no revision items remaining. FAIL otherwise (if any revision items remain unaddressed or if the proof still requires significant modifications).",
    )


class FactorCode(BaseModel):
    """
    Factor Code
    """

    code: str = Field(
        description="The code implementation of the factor formula in Python.",
    )
