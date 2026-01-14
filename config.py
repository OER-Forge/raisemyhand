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

    # Determine which env file to load based on ENV variable or file existence
    # Priority: ENV variable (from docker-compose) > .env file > .env.demo
    def _get_env_file() -> str:
        """Determine which environment file to load"""
        env = os.getenv("ENV", "").lower()

        # If ENV is explicitly set to production, load .env.production
        if env == "production":
            return ".env.production"
        # If ENV is demo or .env.demo exists, use it
        elif env == "demo" or os.path.exists(".env.demo"):
            return ".env.demo"
        # Default to .env for development
        elif os.path.exists(".env"):
            return ".env"
        # Fallback to .env.demo if nothing else exists
        else:
            return ".env.demo"

    model_config = SettingsConfigDict(
        env_file=_get_env_file(),
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
    # Use sentinel values that are clearly defaults and can be validated
    secret_key: str = "CHANGE_THIS_SECRET_KEY_TO_A_RANDOM_32_CHAR_VALUE"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 hours default

    # Security Configuration - Admin
    admin_username: str = "admin"
    admin_password: Optional[str] = None

    # Security Configuration - CSRF
    # Use sentinel values that are clearly defaults and can be validated
    csrf_secret: str = "CHANGE_THIS_CSRF_SECRET_TO_A_RANDOM_32_CHAR_VALUE"
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

    @property
    def is_demo(self) -> bool:
        """Check if running in demo mode"""
        return self.demo_mode or self.env.lower() == "demo"

    def validate_production_config(self) -> tuple[list[str], list[str]]:
        """Validate production configuration. Returns (errors, warnings)"""
        errors = []
        warnings = []

        if self.is_production:
            # Critical errors
            if self.database_url.startswith("sqlite"):
                errors.append(
                    "SQLite is NOT supported in production! "
                    "Use PostgreSQL for 75+ concurrent users. "
                    "Set DATABASE_URL=postgresql://... in .env.production"
                )

            # Check if SECRET_KEY is still the default sentinel value
            if self.secret_key.startswith("CHANGE_THIS_SECRET_KEY") or len(self.secret_key) < 32:
                errors.append(
                    "SECRET_KEY must be set to a random 32+ character value in .env.production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )

            # Check if CSRF_SECRET is still the default sentinel value
            if self.csrf_secret.startswith("CHANGE_THIS_CSRF_SECRET") or len(self.csrf_secret) < 32:
                errors.append(
                    "CSRF_SECRET must be set to a random 32+ character value in .env.production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )

            if not self.admin_password:
                errors.append("ADMIN_PASSWORD must be set to a strong password in .env.production")

            if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
                warnings.append("BASE_URL contains localhost/127.0.0.1 - update to your actual domain for production")

            if self.debug:
                warnings.append("DEBUG is True in production - should be False for security")

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
