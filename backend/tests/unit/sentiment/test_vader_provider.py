from veya.infrastructure.sentiment.vader import VaderSentimentProvider


def test_vader_classifies_positive_text() -> None:
    result = VaderSentimentProvider().classify("I absolutely love this reel!")

    assert result.label == "positive"
    assert result.compound_score > 0
    assert result.provider == "vader"


def test_vader_classifies_negative_text() -> None:
    result = VaderSentimentProvider().classify("This is terrible and I hate it.")

    assert result.label == "negative"
    assert result.compound_score < 0


def test_vader_classifies_neutral_text() -> None:
    result = VaderSentimentProvider().classify("The video was uploaded today.")

    assert result.label == "neutral"
