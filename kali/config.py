"""Central configuration management for Kali."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import (
    EmailStr,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root: parent directory of the kali package.
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Validated application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Project identification
    project_name: str = Field(
        min_length=1,
        validation_alias="PROJECT_NAME",
    )

    # MongoDB connection
    mongodb_uri: SecretStr = Field(
        min_length=1,
        validation_alias="MONGODB_URI",
    )

    # Local backup settings
    backup_root: Path = Field(
        default=BASE_DIR / "backups",
        validation_alias="BACKUP_ROOT",
    )
    retention_days: int = Field(
        default=3,
        ge=1,
        validation_alias="RETENTION_DAYS",
    )

    # Backup schedule
    backup_interval_hours: int = Field(
        default=6,
        ge=1,
        validation_alias="BACKUP_INTERVAL_HOURS",
    )

    # Supported backup modes
    backup_mode: Literal["database", "cluster"] = Field(
        default="database",
        validation_alias="BACKUP_MODE",
    )
    database_name: str = Field(
        default="",
        validation_alias="DATABASE_NAME",
    )

    # AWS S3 settings
    s3_bucket: str = Field(
        default="",
        validation_alias="S3_BUCKET",
    )
    s3_prefix: str = Field(
        default="mongodb-backups",
        validation_alias="S3_PREFIX",
    )
    s3_retention_days: int = Field(
        default=30,
        ge=1,
        validation_alias="S3_RETENTION_DAYS",
    )
    aws_region: str = Field(
        default="ap-south-1",
        validation_alias="AWS_REGION",
    )

    # Email notifications
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

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        validation_alias="LOG_LEVEL",
    )
    log_file: str = Field(
        default="",
        validation_alias="LOG_FILE",
    )

    @field_validator(
        "project_name",
        "s3_bucket",
        "s3_prefix",
        "database_name",
        "notification_sender",
        "notification_recipient",
        "log_file",
        mode="before",
    )
    @classmethod
    def strip_strings(cls, value: object) -> object:
        """Strip surrounding whitespace from string configuration values."""
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("project_name")
    @classmethod
    def validate_project_name(cls, value: str) -> str:
        """Reject an empty project name."""
        if not value:
            raise ValueError("PROJECT_NAME cannot be empty.")
        return value

    @field_validator("mongodb_uri")
    @classmethod
    def validate_mongodb_uri(cls, value: SecretStr) -> SecretStr:
        """Validate the MongoDB connection URI scheme."""
        uri = value.get_secret_value().strip()

        if not uri.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError(
                "MONGODB_URI must start with mongodb:// or mongodb+srv://"
            )

        return SecretStr(uri)

    @field_validator("backup_mode", mode="before")
    @classmethod
    def normalize_backup_mode(cls, value: object) -> object:
        """Normalize the backup mode before Literal validation."""
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        """Normalize the configured logging level."""
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @model_validator(mode="after")
    def validate_backup_configuration(self) -> "Settings":
        """Validate configuration requirements based on selected modes."""

        if self.backup_mode == "database":
            database_name = self.database_name or self.uri_database_name

            if not database_name:
                raise ValueError(
                    "DATABASE_NAME is required in database mode unless "
                    "the MongoDB URI contains a database name."
                )

        if self.email_notifications_enabled:
            if not self.notification_sender or not self.notification_recipient:
                raise ValueError(
                    "NOTIFICATION_SENDER and NOTIFICATION_RECIPIENT are "
                    "required when EMAIL_NOTIFICATIONS_ENABLED is true."
                )

            try:
                EmailStr._validate(self.notification_sender)
                EmailStr._validate(self.notification_recipient)
            except Exception as exc:
                raise ValueError(
                    "Notification sender and recipient must be valid email addresses."
                ) from exc

        return self

    @property
    def uri_database_name(self) -> str:
        """Extract the database name from the MongoDB URI path."""
        from urllib.parse import urlsplit

        uri = self.mongodb_uri.get_secret_value()
        parsed = urlsplit(uri)

        # MongoDB SRV URIs may contain query parameters, but the database
        # name is the path component after the host.
        return parsed.path.lstrip("/").split("/")[0].strip()

    @property
    def effective_database_name(self) -> str:
        """Return the explicit database name or the name from the URI."""
        return self.database_name or self.uri_database_name

    @property
    def s3_enabled(self) -> bool:
        """Return whether S3 uploads are configured."""
        return bool(self.s3_bucket)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached, validated settings instance."""
    return Settings()
