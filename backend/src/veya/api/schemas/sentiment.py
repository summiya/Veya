from pydantic import BaseModel


class AnalyzeSentimentResponse(BaseModel):
    analyzed_comments: int


class SentimentSummaryResponse(BaseModel):
    total: int
    positive: int
    neutral: int
    negative: int
    positive_percentage: float
    neutral_percentage: float
    negative_percentage: float
