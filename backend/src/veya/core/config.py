from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Veya"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://veya:veya@db:5432/veya"

    jwt_secret_key: str = "development-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
