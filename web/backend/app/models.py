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
    test_case: str | None = None
    rationale: str | None = None


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


class Partial(Model):
    profile: Profile | None = None
    regulations: list[RegulationDecision] | None = None
    paragraph_count: int | None = None
    requirements: list[Requirement] | None = None


class PipelineEvent(Model):
    step: Literal["profile", "selection", "paragraphs", "requirements", "done"]
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


class AskRequest(Model):
    question: str = Field(max_length=1000)
    selection: str = Field(max_length=6000)
    requirements: list[Requirement] = Field(max_length=2000)


class AskAnswer(Model):
    sentences: list[BriefSentence]
    cost_usd: float
    spent_usd: float
    budget_usd: float
