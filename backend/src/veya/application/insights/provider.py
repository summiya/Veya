from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class InsightComment:
    text: str
    sentiment_label: str | None
    safety_label: str


@dataclass(frozen=True)
class AudienceInsightsResult:
    summary: str
    what_people_loved: list[str]
    constructive_feedback: list[str]
    recurring_complaints: list[str]
    common_questions: list[str]
    content_suggestions: list[str]
    provider: str
    model: str


class AudienceInsightsProvider(Protocol):
    def generate(self, comments: list[InsightComment]) -> AudienceInsightsResult:
        ...
