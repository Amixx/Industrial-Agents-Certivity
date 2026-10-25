from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_serializer
from pydantic.alias_generators import to_camel


class Model(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    def dump(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)


class Source(Model):
    regulation: str
    version: str
    page: int
    paragraph: str


class Requirement(Model):
    id: str
    text: str
    source: Source
    quote: str | None = None
    test_case: str | None = None
    rationale: str | None = None
    confidence: float | None = None
    """The brain's probability that its paragraph is cited."""


class Profile(Model):
    product_type: str
    vehicle_category: str
    parts: list[str]
    functions: list[str]
    materials: list[str]


class RegulationDecision(Model):
    regulation: str
    version: str
    title: str
    included: bool
    reason: str
    requirement_count: int


class ModelCost(Model):
    model: str
    calls: int
    input: int
    output: int
    cache_write: int
    cache_read: int
    cost_usd: float


class RunCost(Model):
    total_usd: float
    models: list[ModelCost]


class CutParagraph(Model):
    """A paragraph the run cut, with its score and the cut it fell under."""

    regulation: str
    version: str
    page: int
    paragraph: str
    text: str | None = None
    """The start of the paragraph, so a reader can tell what it is about."""
    score: float
    cut: float
    stage: Literal["paragraph", "section", "confidence"]


class Assessment(Model):
    id: str
    created_at: str
    case_name: str | None = None
    spec: str
    image_url: str | None = None
    profile: Profile
    regulations: list[RegulationDecision]
    requirements: list[Requirement]
    status: Literal["running", "complete", "failed"]
    cost: RunCost | None = None
    below_cut: list[CutParagraph] | None = None


class Partial(Model):
    profile: Profile | None = None
    regulations: list[RegulationDecision] | None = None
    paragraph_count: int | None = None
    requirements: list[Requirement] | None = None


class PipelineEvent(Model):
    step: Literal["profile", "selection", "paragraphs", "requirements", "done", "failed"]
    message: str
    progress: float
    assessment_id: str | None = None
    partial: Partial | None = None


class ChangeSource(Model):
    page: int
    paragraph: str


class RequirementChange(Model):
    requirement_id: str | None = None
    change: Literal["modified", "removed", "added"]
    old_text: str | None = None
    new_text: str | None = None
    reason: str
    source: ChangeSource

    @model_serializer(mode="wrap")
    def _keep_requirement_id(self, handler: Any) -> dict[str, Any]:
        data: dict[str, Any] = handler(self)
        data.setdefault("requirementId", None)
        return data


class RegulationUpdate(Model):
    regulation: str
    from_version: str
    to_version: str
    changes: list[RequirementChange]
    applied: bool | None = None


class BriefSentence(Model):
    text: str
    cites: list[str]


class BriefSection(Model):
    title: str
    sentences: list[BriefSentence]


class Brief(Model):
    sections: list[BriefSection]


class BriefRequest(Model):
    requirements: list[Requirement]
    write: bool = False
    """Write the brief if none is cached; otherwise only a cached brief is returned."""


class AskRequest(Model):
    question: str = Field(max_length=1000)
    selection: str = Field(max_length=6000)
    requirements: list[Requirement] = Field(max_length=2000)


class ReadRequest(Model):
    assessment_id: str = Field(max_length=64)
    text: str = Field(max_length=6000)


class ReadAnswer(Model):
    """What will be read aloud: the selection without labels, and its voice when there is one."""

    text: str
    speech_id: str | None = None


class AskAnswer(Model):
    sentences: list[BriefSentence]
    cost_usd: float
    spent_usd: float
    budget_usd: float
    # Set when the server can voice the answer with ElevenLabs: GET /api/speak/{speech_id}.
    speech_id: str | None = None


class CoverageRow(Model):
    id: str
    text: str
    source: Source


class Nearest(CoverageRow):
    similarity: float
    paired_with: str | None = None
    """The expert row the judge paired this row with instead, if any."""


class Miss(CoverageRow):
    reason: Literal["below_cut", "split_finer", "worded_differently"]
    score: float | None = None
    cut: float | None = None
    stage: Literal["paragraph", "section", "confidence"] | None = None
    nearest: Nearest | None = None


class Extra(CoverageRow):
    on_expert_paragraph: bool


class LocalScore(Model):
    expected: int
    submitted: int
    matched: int
    precision: float
    recall: float
    f2: float


class PlatformUpload(Model):
    at: str
    """As the run log in out/README.md writes it, with its time zone."""
    f2: float
    matched: int | None = None
    """Expert rows matched; None on the held-out case, whose expert answer is hidden."""
    precision: float | None = None
    recall: float | None = None


class PlatformScore(Model):
    file: str
    rows: int
    uploads: list[PlatformUpload]


class NearCut(Model):
    source: Source
    text: str | None = None
    score: float
    cut: float | None = None
    stage: Literal["paragraph", "section", "confidence"] | None = None
    kept: bool


class Coverage(Model):
    case: str | None
    has_answer: bool
    local: LocalScore | None = None
    platform: PlatformScore | None = None
    missed: list[Miss] = []
    extra: list[Extra] = []
    excluded: list[RegulationDecision]
    near_cut: list[NearCut] = []
    expert_copies: int = 0
    """Expert rows this assessment holds word for word; all of them means it measures nothing."""
    engine_run: str | None = None
    """A stored engine run on the same case, to compare instead."""
