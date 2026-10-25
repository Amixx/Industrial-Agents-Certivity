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
    source: ChangeSource | None = None
    """The paragraph in the new version; removed rows have none."""
    new_id: str | None = None
    """The id an added requirement gets when the update is applied."""
    old_paragraph: str | None = None
    """The paragraph the old requirement cites, on modified and removed rows."""
    hunk: str | None = None
    """The id of the paragraph hunk this change comes from."""

    @model_serializer(mode="wrap")
    def _keep_requirement_id(self, handler: Any) -> dict[str, Any]:
        data: dict[str, Any] = handler(self)
        data.setdefault("requirementId", None)
        return data


HunkStatus = Literal["amended", "moved and amended", "new", "deleted"]


class HunkRow(Model):
    kind: Literal["unchanged", "amended", "new", "deleted"]
    segments: list[tuple[Literal["same", "del", "ins"], str]]


class Hunk(Model):
    """One changed paragraph of the regulation, as a unified word diff of its units."""

    id: str
    label: str
    old_label: str | None = None
    page: int
    """The page in the new version (the old one for a deleted paragraph)."""
    old_page: int | None = None
    status: HunkStatus
    heading: str = ""
    rows: list[HunkRow]
    added_words: int
    removed_words: int
    cited_by: list[str] = []
    """Requirements that cite this paragraph or one of its ancestors."""
    changes: list[str] = []
    """Ids of the requirement changes (requirement id, or new id for added rows) it causes."""


class StepSeconds(Model):
    parse: float
    align: float
    map: float


class RunStats(Model):
    old_paragraphs: int
    new_paragraphs: int
    old_units: int
    new_units: int
    unchanged_share: float
    amended: int
    new: int
    deleted: int
    renumbered: int
    requirements: int
    cited_paragraphs: int
    changed_cited_paragraphs: int
    seconds: StepSeconds


class UpdateRun(Model):
    """One comparison of a cited regulation with a newer version, for one assessment."""

    id: str
    assessment_id: str
    regulation: str
    title: str
    from_version: str
    to_version: str
    created_at: str
    identified_by: Literal["sha256", "first page", "corpus"]
    file_name: str
    stats: RunStats
    hunks: list[Hunk]
    changes: list[RequirementChange]
    applied: bool = False


class CitedRegulation(Model):
    regulation: str
    title: str
    version: str
    latest: str | None = None
    """The newest version in the corpus when it is newer than the cited one."""
    requirement_count: int
    run: str | None = None
    """A stored run that compares the cited version with `latest`."""
    applied_run: str | None = None
    """The run applied to reach the cited version, if any."""


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


class AskAnswer(Model):
    sentences: list[BriefSentence]
    cost_usd: float
    spent_usd: float
    budget_usd: float
