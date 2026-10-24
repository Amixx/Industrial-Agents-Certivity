"""Shared records passed between pipeline steps."""

from typing import Literal

from pydantic import BaseModel, Field

Role = Literal["base", "latest"]
ConditionType = Literal["none", "when", "while", "where", "if"]
Modality = Literal["shall", "shall not", "must", "must not", "may", "other"]


class Paragraph(BaseModel):
    """One numbered paragraph of a regulation PDF, with the page its label sits on."""

    id: str  # "UN R148|1.6.0|5.5.7"; unique within the corpus
    regulation: str  # "UN R148"
    version: str  # version_label from regulations/index.json
    role: Role
    label: str  # citation label: "5.5.7", "Annex 3 1.2", "Annex 6 Part 4 3", "Annex 3"
    number: str  # the local number ("1.2"), empty for an annex or part heading
    annex: str | None = None  # "Annex 6 Part 4" when inside an annex
    page: int  # PDF page of the label
    page_end: int  # PDF page where the text ends
    heading: str | None = None  # short title on the label line, e.g. "Colour:"
    text: str  # full text, stitched across page breaks
    page_breaks: list[int] = Field(
        default_factory=list
    )  # offsets in `text` where a new page starts
    parent: str | None = None  # id of the parent paragraph
    path: list[str] = Field(
        default_factory=list
    )  # ids from the top-level ancestor down to the parent

    def page_at(self, offset: int) -> int:
        return self.page + sum(1 for b in self.page_breaks if b <= offset)


class Obligation(BaseModel):
    """One candidate requirement: a single shall-sentence (or clause) of a paragraph."""

    id: str  # paragraph id + "#n"
    paragraph_id: str
    regulation: str
    version: str
    label: str
    page: int
    sentence: str  # the source sentence, verbatim
    modality: Modality
    subject: str | None = None
    condition_type: ConditionType = "none"
    condition: str | None = None
    text: str  # rendered requirement text
    score: float | None = None
    rationale: str | None = None


class ProductProfile(BaseModel):
    product: str
    vehicle_categories: list[str] = Field(default_factory=list)  # ["M1"]
    functions: list[str] = Field(default_factory=list)  # ["stop lamp", "reversing lamp"]
    parts: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    electronics: bool = False
    keywords: list[str] = Field(
        default_factory=list
    )  # regulation vocabulary for the parts/functions


class RegulationChoice(BaseModel):
    regulation: str
    version: str
    probability: float
    selected: bool
    rationale: str
