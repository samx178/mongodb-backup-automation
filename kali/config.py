"""Central configuration management for Kali."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = Field(min_length=1, validation_alias="PROJECT_NAME")
    mongodb_uri: SecretStr = Field(
        min_length=1,
        validation_alias="MONGODB_URI",
    )

    backup_root: Path = Field(
        default=Path("/opt/mongodb-backups"),
        validation_alias="BACKUP_ROOT",
    )
    retention_days: int = Field(default=3, ge=1, validation_alias="RETENTION_DAYS")
    backup_interval_hours: int = Field(
        default=6,
        ge=1,
        validation_alias="BACKUP_INTERVAL_HOURS",
    )

    s3_bucket: str = Field(default="", validation_alias="S3_BUCKET")
    s3_prefix: str = Field(
        default="mongodb-backups",
        validation_alias="S3_PREFIX",
    )
    s3_retention_days: int = Field(
        default=30,
        ge=1,
        validation_alias="S3_RETENTION_DAYS",
    )
    aws_region: str = Field(default="ap-south-1", validation_alias="AWS_REGION")

    email_notifications_enabled: bool = Field(
        default=False,
        validation_alias="EMAIL_NOTIFICATIONS_ENABLED",
    )
    notification_sender: str = Field(
        default="",
        validation_alias="NOTIFICATION_SENDER",
    )
    notification_recipient: str = Field(
        default="",
        validation_alias="NOTIFICATION_RECIPIENT",
    )

    @field_validator("project_name", "s3_bucket", "s3_prefix")
    @classmethod
    def strip_strings(cls, value: str) -> str:
        """Remove accidental whitespace from string settings."""
        return value.strip()

    @field_validator("mongodb_uri")
    @classmethod
    def validate_mongodb_uri(cls, value: SecretStr) -> SecretStr:
        """Accept standard MongoDB connection URI schemes."""
        uri = value.get_secret_value().strip()
        if not uri.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError(
                "MONGODB_URI must start with mongodb:// or mongodb+srv://"
            )
        return SecretStr(uri)

    @property
    def s3_enabled(self) -> bool:
        """Return whether remote S3 backups are configured."""
        return bool(self.s3_bucket)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached, validated settings instance."""
    return Settings()