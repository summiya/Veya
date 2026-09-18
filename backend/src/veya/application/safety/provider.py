from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SafetyClassification:
    primary_label: str
    constructive_score: float
    toxic_score: float
    severe_abuse_score: float
    spam_score: float
    should_shield: bool
    provider: str


class SafetyProvider(Protocol):
    def classify(self, text: str) -> SafetyClassification:
        ...
