from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Veya"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://veya:veya@db:5432/veya"

    jwt_secret_key: str = "development-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    password_reset_expire_minutes: int = 30

    mail_provider: str = "console"
    resend_api_key: str = ""
    resend_api_url: str = "https://api.resend.com/emails"
    mail_from: str = "Veya <onboarding@resend.dev>"

    instagram_client_id: str = ""
    instagram_client_secret: str = ""
    instagram_redirect_uri: str = "http://localhost:8000/api/integrations/instagram/callback"
    instagram_authorize_url: str = "https://www.instagram.com/oauth/authorize"
    instagram_token_url: str = "https://api.instagram.com/oauth/access_token"
    instagram_graph_url: str = "https://graph.instagram.com"
    instagram_scopes: str = (
        "instagram_business_basic,instagram_business_manage_comments"
    )
    instagram_token_encryption_key: str = ""
    frontend_app_url: str = "http://localhost:5173"

    openai_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"
    openai_responses_url: str = "https://api.openai.com/v1/responses"
    insights_max_comments: int = 200
    insights_max_comment_chars: int = 600

    redis_url: str = "redis://redis:6379/0"
    background_sync_interval_minutes: int = 15
    background_sync_scheduler_seconds: int = 60
    background_sync_max_retries: int = 3
    background_sync_retry_seconds: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
