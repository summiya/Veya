import json

import httpx

from veya.application.insights.provider import (
    AudienceInsightsResult,
    InsightComment,
)
from veya.core.config import settings


class AudienceInsightsProviderError(RuntimeError):
    pass


class OpenAIAudienceInsightsProvider:
    provider_name = "openai"

    def __init__(
        self,
        *,
        http_client: httpx.Client | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.http = http_client or httpx.Client(timeout=45.0)
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.model = model or settings.openai_model

    def generate(self, comments: list[InsightComment]) -> AudienceInsightsResult:
        if not self.api_key:
            raise AudienceInsightsProviderError(
                "OPENAI_API_KEY must be configured to generate AI audience insights"
            )

        prepared_comments = [
            {
                "text": item.text[: settings.insights_max_comment_chars],
                "sentiment": item.sentiment_label,
                "safety": item.safety_label,
            }
            for item in comments[: settings.insights_max_comments]
        ]

        schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "what_people_loved": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "constructive_feedback": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "recurring_complaints": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "common_questions": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "content_suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": [
                "summary",
                "what_people_loved",
                "constructive_feedback",
                "recurring_complaints",
                "common_questions",
                "content_suggestions",
            ],
            "additionalProperties": False,
        }

        prompt = (
            "Analyze these Instagram audience comments for a creator. "
            "Use only the supplied comments. Do not quote abusive content. "
            "Summarize recurring themes, not isolated comments. "
            "Keep each list concise and actionable. Comments:\n"
            + json.dumps(prepared_comments, ensure_ascii=False)
        )

        try:
            response = self.http.post(
                settings.openai_responses_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "input": [
                        {
                            "role": "system",
                            "content": (
                                "You generate concise creator audience insights from "
                                "pre-filtered social comments. Never infer facts that "
                                "are not supported by the comments."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "name": "audience_insights",
                            "schema": schema,
                            "strict": True,
                        }
                    },
                },
            )
            response.raise_for_status()
            body = response.json()
            output_text = self._extract_output_text(body)
            parsed = json.loads(output_text)
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise AudienceInsightsProviderError(
                "AI audience insight generation failed"
            ) from exc

        return AudienceInsightsResult(
            summary=str(parsed["summary"]),
            what_people_loved=list(parsed["what_people_loved"]),
            constructive_feedback=list(parsed["constructive_feedback"]),
            recurring_complaints=list(parsed["recurring_complaints"]),
            common_questions=list(parsed["common_questions"]),
            content_suggestions=list(parsed["content_suggestions"]),
            provider=self.provider_name,
            model=self.model,
        )

    @staticmethod
    def _extract_output_text(body: dict) -> str:
        for item in body.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") == "output_text" and content.get("text"):
                    return str(content["text"])
        raise AudienceInsightsProviderError("OpenAI response did not contain output text")
