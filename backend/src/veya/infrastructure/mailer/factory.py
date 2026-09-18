from veya.core.config import settings
from veya.infrastructure.mailer.console import ConsoleMailer
from veya.infrastructure.mailer.provider import Mailer
from veya.infrastructure.mailer.resend import ResendMailer


def create_mailer() -> Mailer:
    if settings.mail_provider.lower() == "resend":
        return ResendMailer()
    return ConsoleMailer()
