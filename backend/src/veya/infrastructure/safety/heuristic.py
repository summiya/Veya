import re

from veya.application.safety.provider import SafetyClassification


class HeuristicSafetyProvider:
    name = "heuristic-v1"

    _severe_patterns = (
        "kill yourself",
        "go die",
        "hope you die",
        "i will kill",
        "you should die",
    )
    _toxic_terms = (
        "idiot",
        "stupid",
        "ugly",
        "loser",
        "trash",
        "disgusting",
        "shut up",
        "hate you",
    )
    _constructive_terms = (
        "could you",
        "you could",
        "should",
        "maybe",
        "would be better",
        "please",
        "next time",
        "audio",
        "volume",
        "too loud",
        "too low",
        "wish",
        "try",
    )
    _spam_terms = (
        "dm me",
        "follow me",
        "check my profile",
        "promo",
        "promotion",
        "giveaway",
        "click link",
        "link in bio",
    )

    def classify(self, text: str) -> SafetyClassification:
        normalized = " ".join(text.lower().split())

        severe_score = 0.98 if any(term in normalized for term in self._severe_patterns) else 0.0
        toxic_matches = sum(term in normalized for term in self._toxic_terms)
        toxic_score = min(0.96, toxic_matches * 0.42) if toxic_matches else 0.0

        spam_signals = sum(term in normalized for term in self._spam_terms)
        spam_signals += 1 if re.search(r"https?://|www\.", normalized) else 0
        spam_signals += 1 if normalized.count("#") >= 4 else 0
        spam_signals += 1 if normalized.count("@") >= 4 else 0
        spam_score = min(0.95, spam_signals * 0.45) if spam_signals else 0.0

        constructive_matches = sum(term in normalized for term in self._constructive_terms)
        constructive_score = (
            min(0.88, 0.46 + constructive_matches * 0.12)
            if constructive_matches and toxic_score == 0 and severe_score == 0 and spam_score < 0.7
            else 0.0
        )

        if severe_score >= 0.9:
            label = "severe_abuse"
        elif spam_score >= 0.7:
            label = "spam"
        elif toxic_score >= 0.4:
            label = "toxic"
        elif constructive_score >= 0.5:
            label = "constructive"
        else:
            label = "safe"

        return SafetyClassification(
            primary_label=label,
            constructive_score=constructive_score,
            toxic_score=toxic_score,
            severe_abuse_score=severe_score,
            spam_score=spam_score,
            should_shield=label in {"toxic", "severe_abuse"},
            provider=self.name,
        )
