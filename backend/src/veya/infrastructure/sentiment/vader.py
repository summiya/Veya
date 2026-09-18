from vader import SentimentIntensityAnalyzer

from veya.application.sentiment.provider import SentimentClassification


class VaderSentimentProvider:
    name = "vader"

    def __init__(self) -> None:
        self.analyzer = SentimentIntensityAnalyzer()

    def classify(self, text: str) -> SentimentClassification:
        scores = self.analyzer.polarity_scores(text)

        compound = float(scores["compound"])
        if compound >= 0.05:
            label = "positive"
            confidence = float(scores["pos"])
        elif compound <= -0.05:
            label = "negative"
            confidence = float(scores["neg"])
        else:
            label = "neutral"
            confidence = float(scores["neu"])

        return SentimentClassification(
            label=label,
            confidence=confidence,
            positive_score=float(scores["pos"]),
            neutral_score=float(scores["neu"]),
            negative_score=float(scores["neg"]),
            compound_score=compound,
            provider=self.name,
        )
