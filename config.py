"""
Configuration management for RaiseMyHand using Pydantic Settings
Loads settings from environment variables with sensible defaults
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import secrets
import os


class Settings(BaseSettings):
    """Application configuration with environment variable support"""

    # Prefer .env (for local dev) over .env.demo (for Docker demo)
    _env_file = ".env" if os.path.exists(".env") else ".env.demo"

    model_config = SettingsConfigDict(
        env_file=_env_file,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Environment
    env: str = "development"  # development, production, testing

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    base_url: str = "http://localhost:8000"
    debug: bool = True

    # Database Configuration
    database_url: str = "sqlite:///./data/raisemyhand.db"

    # Security Configuration - JWT
    secret_key: str = secrets.token_urlsafe(32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 hours default

    # Security Configuration - Admin
    admin_username: str = "admin"
    admin_password: Optional[str] = None

    # Security Configuration - CSRF
    csrf_secret: str = secrets.token_urlsafe(32)
    csrf_token_expiry: int = 3600  # 1 hour

    # Application Configuration
    timezone: str = "UTC"
    enable_auth: bool = True

    # Rate Limiting
    rate_limit_enabled: bool = True

    # Demo Mode
    demo_mode: bool = False

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.env.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.env.lower() == "development"

    def validate_production_config(self) -> tuple[list[str], list[str]]:
        """Validate production configuration. Returns (errors, warnings)"""
        errors = []
        warnings = []

        if self.is_production:
            # Critical errors
            if self.secret_key == secrets.token_urlsafe(32) or len(self.secret_key) < 32:
                errors.append("SECRET_KEY must be explicitly set and at least 32 characters in production")

            if self.csrf_secret == secrets.token_urlsafe(32) or len(self.csrf_secret) < 32:
                errors.append("CSRF_SECRET must be explicitly set and at least 32 characters in production")

            if not self.admin_password:
                errors.append("ADMIN_PASSWORD must be set in production")

            if "localhost" in self.base_url:
                errors.append("BASE_URL should not contain 'localhost' in production")

            if self.debug:
                warnings.append("DEBUG is True in production - should be False for security")

            if self.database_url.startswith("sqlite"):
                warnings.append("Using SQLite in production - consider PostgreSQL for better performance")

        return errors, warnings

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# Global settings instance
settings = Settings()


# Validate critical settings
if not settings.admin_password:
    import warnings
    warnings.warn(
        "WARNING: ADMIN_PASSWORD not set! "
        "Admin panel will be inaccessible. "
        "Set ADMIN_PASSWORD environment variable or create Docker secret.",
        UserWarning
    )
