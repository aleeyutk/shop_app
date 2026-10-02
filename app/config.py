import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "NovaShop"
    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-key-change-in-production-12345"
    BASE_URL: str = "http://localhost:8000"

    # Database Configuration (Neon/Supabase or local SQLite)
    DATABASE_URL: str = "sqlite:///./shop.db"

    # Google Cloud OAuth Credentials
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Mailgun Email Configuration
    MAILGUN_API_KEY: str = ""
    MAILGUN_DOMAIN: str = ""
    MAILGUN_FROM_EMAIL: str = "NovaShop <orders@novashop.store>"
    MAILGUN_BASE_URL: str = "https://api.mailgun.net/v3"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def normalized_database_url(self) -> str:
        """
        Normalize DATABASE_URL for SQLAlchemy 2.0 compatibility.
        Neon and Supabase often output URLs starting with postgres:// instead of postgresql://.
        """
        url = self.DATABASE_URL.strip()
        if not url:
            return "sqlite:///./shop.db"
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    @property
    def is_postgres(self) -> bool:
        return self.normalized_database_url.startswith("postgresql")

    @property
    def is_google_auth_configured(self) -> bool:
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)

    @property
    def is_mailgun_configured(self) -> bool:
        return bool(self.MAILGUN_API_KEY and self.MAILGUN_DOMAIN)


@lru_cache
def get_settings() -> Settings:
    return Settings()
