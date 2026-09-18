import logging

from veya.infrastructure.mailer.provider import MailMessage


logger = logging.getLogger(__name__)


class ConsoleMailer:
    def send(self, message: MailMessage) -> None:
        logger.info(
            "Development mail to=%s subject=%s body=%s",
            message.to,
            message.subject,
            message.html,
        )
