from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AudienceInsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    summary: str
    what_people_loved: list[str]
    constructive_feedback: list[str]
    recurring_complaints: list[str]
    common_questions: list[str]
    content_suggestions: list[str]
    provider: str
    model: str
    source_comment_count: int
    generated_at: datetime
