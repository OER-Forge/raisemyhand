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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    base_url: str = "http://localhost:8000"

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Try to load admin password from Docker secret file if not in env
        if not self.admin_password:
            secret_file = "/run/secrets/admin_password"
            if os.path.exists(secret_file):
                with open(secret_file, 'r') as f:
                    self.admin_password = f.read().strip()

    class Config:
        """Pydantic config"""
        env_prefix = ""  # No prefix for environment variables


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
