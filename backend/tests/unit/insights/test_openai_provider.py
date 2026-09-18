import json

import httpx

from veya.application.insights.provider import InsightComment
from veya.infrastructure.insights.openai import OpenAIAudienceInsightsProvider


def test_openai_provider_uses_structured_output_and_parses_result() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content.decode()))
        return httpx.Response(
            200,
            json={
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": json.dumps(
                                    {
                                        "summary": "Audience response is mostly positive.",
                                        "what_people_loved": ["Editing style"],
                                        "constructive_feedback": ["Increase audio volume"],
                                        "recurring_complaints": ["Low audio"],
                                        "common_questions": ["Where is this location?"],
                                        "content_suggestions": ["Share location details"],
                                    }
                                ),
                            }
                        ],
                    }
                ]
            },
        )

    provider = OpenAIAudienceInsightsProvider(
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        api_key="fake-test-key",
        model="gpt-test",
    )

    result = provider.generate(
        [
            InsightComment(
                text="Love the editing",
                sentiment_label="positive",
                safety_label="safe",
            )
        ]
    )

    assert captured["model"] == "gpt-test"
    assert captured["text"]["format"]["type"] == "json_schema"
    assert captured["text"]["format"]["strict"] is True
    assert result.summary == "Audience response is mostly positive."
    assert result.what_people_loved == ["Editing style"]
    assert result.provider == "openai"
    assert result.model == "gpt-test"
