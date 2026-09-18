import httpx

from veya.core.config import settings
from veya.infrastructure.mailer.provider import MailMessage


class MailerDeliveryError(RuntimeError):
    pass


class ResendMailer:
    def __init__(self, http_client: httpx.Client | None = None) -> None:
        self.http = http_client or httpx.Client(timeout=15.0)

    def send(self, message: MailMessage) -> None:
        if not settings.resend_api_key:
            raise MailerDeliveryError("RESEND_API_KEY is not configured")

        try:
            response = self.http.post(
                settings.resend_api_url,
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": settings.mail_from,
                    "to": [message.to],
                    "subject": message.subject,
                    "html": message.html,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise MailerDeliveryError("Transactional email delivery failed") from exc
