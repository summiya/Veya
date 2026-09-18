import httpx

from veya.core.config import settings
from veya.infrastructure.mailer.provider import MailMessage
from veya.infrastructure.mailer.resend import ResendMailer


def test_resend_mailer_posts_transactional_email() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers.get("Authorization")
        captured["body"] = request.content.decode()
        return httpx.Response(200, json={"id": "email-test"})

    original_key = settings.resend_api_key
    original_from = settings.mail_from
    try:
        settings.resend_api_key = "fake-test-key"
        settings.mail_from = "Veya <test@example.com>"

        mailer = ResendMailer(
            http_client=httpx.Client(transport=httpx.MockTransport(handler))
        )
        mailer.send(
            MailMessage(
                to="creator@example.com",
                subject="Reset your Veya password",
                html="<p>Reset</p>",
            )
        )
    finally:
        settings.resend_api_key = original_key
        settings.mail_from = original_from

    assert captured["authorization"] == "Bearer fake-test-key"
    assert '"to":["creator@example.com"]' in captured["body"].replace(" ", "")
    assert '"subject":"ResetyourVeyapassword"' not in captured["body"].replace(" ", "")
    assert "Reset your Veya password" in captured["body"]
