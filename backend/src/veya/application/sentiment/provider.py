from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SentimentClassification:
    label: str
    confidence: float
    positive_score: float
    neutral_score: float
    negative_score: float
    compound_score: float
    provider: str


class SentimentProvider(Protocol):
    def classify(self, text: str) -> SentimentClassification:
        ...
