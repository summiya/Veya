from veya.core.config import Settings
from veya.core.runtime import production_configuration_errors


def valid_production_settings() -> Settings:
    return Settings(
        environment="production",
        jwt_secret_key="x" * 48,
        frontend_app_url="https://app.example.com",
        mail_provider="resend",
        resend_api_key="resend-key",
        instagram_client_id="client-id",
        instagram_client_secret="client-secret",
        instagram_redirect_uri=(
            "https://api.example.com/api/integrations/instagram/callback"
        ),
        instagram_token_encryption_key="fernet-key",
    )


def test_valid_production_configuration_has_no_errors() -> None:
    assert production_configuration_errors(valid_production_settings()) == []


def test_production_rejects_development_security_defaults() -> None:
    config = valid_production_settings()
    config.jwt_secret_key = "development-only-change-me"
    config.frontend_app_url = "http://localhost:5173"
    config.instagram_redirect_uri = (
        "http://localhost:8000/api/integrations/instagram/callback"
    )
    config.instagram_token_encryption_key = ""
    config.mail_provider = "console"

    errors = production_configuration_errors(config)

    assert any("JWT_SECRET_KEY" in error for error in errors)
    assert any("FRONTEND_APP_URL" in error for error in errors)
    assert any("INSTAGRAM_REDIRECT_URI" in error for error in errors)
    assert any("INSTAGRAM_TOKEN_ENCRYPTION_KEY" in error for error in errors)
    assert any("MAIL_PROVIDER" in error for error in errors)


def test_development_environment_does_not_require_production_secrets() -> None:
    config = Settings(environment="development")
    assert production_configuration_errors(config) == []
