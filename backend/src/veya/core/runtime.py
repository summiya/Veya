from veya.core.config import Settings, settings


class ProductionConfigurationError(RuntimeError):
    pass


def production_configuration_errors(config: Settings) -> list[str]:
    if config.environment.lower() != "production":
        return []

    errors: list[str] = []

    if (
        config.jwt_secret_key == "development-only-change-me"
        or len(config.jwt_secret_key.encode()) < 32
    ):
        errors.append("JWT_SECRET_KEY must be a production secret of at least 32 bytes")

    if not config.instagram_client_id:
        errors.append("INSTAGRAM_CLIENT_ID is required")

    if not config.instagram_client_secret:
        errors.append("INSTAGRAM_CLIENT_SECRET is required")

    if not config.instagram_token_encryption_key:
        errors.append("INSTAGRAM_TOKEN_ENCRYPTION_KEY is required")

    if not config.instagram_redirect_uri.startswith("https://"):
        errors.append("INSTAGRAM_REDIRECT_URI must use HTTPS in production")

    if config.meta_webhook_enabled and not config.meta_webhook_verify_token:
        errors.append("META_WEBHOOK_VERIFY_TOKEN is required when webhooks are enabled")

    if config.meta_webhook_enabled and not config.meta_webhook_app_secret:
        errors.append("META_WEBHOOK_APP_SECRET is required when webhooks are enabled")

    if not config.frontend_app_url.startswith("https://"):
        errors.append("FRONTEND_APP_URL must use HTTPS in production")

    if config.mail_provider.lower() == "console":
        errors.append("MAIL_PROVIDER cannot be console in production")

    if config.mail_provider.lower() == "resend" and not config.resend_api_key:
        errors.append("RESEND_API_KEY is required when MAIL_PROVIDER=resend")

    if not config.rate_limit_enabled:
        errors.append("RATE_LIMIT_ENABLED must be true in production")

    if not config.trust_proxy_headers:
        errors.append("TRUST_PROXY_HEADERS must be true in production")

    return errors


def validate_runtime_configuration() -> None:
    errors = production_configuration_errors(settings)
    if errors:
        joined = "; ".join(errors)
        raise ProductionConfigurationError(
            f"Invalid production configuration: {joined}"
        )
