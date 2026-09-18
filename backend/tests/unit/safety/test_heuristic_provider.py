from veya.infrastructure.safety.heuristic import HeuristicSafetyProvider


def test_detects_severe_abuse() -> None:
    result = HeuristicSafetyProvider().classify("You should die.")

    assert result.primary_label == "severe_abuse"
    assert result.should_shield is True


def test_detects_toxic_comment() -> None:
    result = HeuristicSafetyProvider().classify("You are an idiot.")

    assert result.primary_label == "toxic"
    assert result.should_shield is True


def test_detects_constructive_feedback() -> None:
    result = HeuristicSafetyProvider().classify(
        "The audio is too low, maybe increase the volume next time."
    )

    assert result.primary_label == "constructive"
    assert result.should_shield is False


def test_detects_spam() -> None:
    result = HeuristicSafetyProvider().classify("DM me for promotion, link in bio.")

    assert result.primary_label == "spam"
    assert result.should_shield is False
