from datetime import datetime

from pydantic import BaseModel


class SafetyAnalyzeResponse(BaseModel):
    analyzed_comments: int


class SafetySummaryResponse(BaseModel):
    total: int
    safe: int
    constructive: int
    toxic: int
    severe_abuse: int
    spam: int
    shielded: int


class SafetyCommentResponse(BaseModel):
    id: int
    text: str
    username: str | None
    commented_at: datetime | None
