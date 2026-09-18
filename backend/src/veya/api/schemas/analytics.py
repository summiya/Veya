from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AudienceHealthSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    analyzed_comment_count: int

    positive: int
    neutral: int
    negative: int

    positive_percentage: float
    neutral_percentage: float
    negative_percentage: float

    constructive: int
    toxic: int
    severe_abuse: int
    spam: int
    shielded: int

    captured_at: datetime


class AudienceTrendResponse(BaseModel):
    points: list[AudienceHealthSnapshotResponse]
    positive_change: float | None
    negative_change: float | None
    shielded_change: int | None
