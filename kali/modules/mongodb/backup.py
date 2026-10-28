"""MongoDB backup execution using mongodump."""

import logging
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from kali.config import Settings, get_settings

logger = logging.getLogger(__name__)


class MongoBackupError(RuntimeError):
    """Raised when a MongoDB backup fails."""


def create_backup(settings: Settings | None = None) -> Path:
    """
    Create a MongoDB logical backup.

    Returns the directory containing the successful backup.
    Supports database and cluster backup modes.
    """
    settings = settings or get_settings()

    mongodump = shutil.which("mongodump")
    if not mongodump:
        raise MongoBackupError(
            "mongodump was not found. Install MongoDB Database Tools."
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = settings.backup_root / settings.project_name / timestamp

    backup_dir.mkdir(parents=True, exist_ok=False)

    command = [
        mongodump,
        f"--uri={settings.mongodb_uri.get_secret_value()}",
        f"--out={backup_dir}",
    ]

    if settings.backup_mode == "database":
        database_name = settings.effective_database_name

        if not database_name:
            raise MongoBackupError(
                "A database name is required for database backup mode."
            )

        command.extend(["--db", database_name])

    logger.info(
        "Starting MongoDB backup: project=%s mode=%s",
        settings.project_name,
        settings.backup_mode,
    )

    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=3600,
        )

        if result.returncode != 0:
            # Avoid logging stderr directly because it may contain
            # connection details or sensitive server information.
            logger.error(
                "mongodump failed with exit code %s.",
                result.returncode,
            )
            raise MongoBackupError(
                f"mongodump failed with exit code {result.returncode}."
            )

        if not any(path.is_file() for path in backup_dir.rglob("*")):
            raise MongoBackupError(
                "mongodump completed but produced no backup files."
            )

        logger.info("MongoDB backup completed: %s", backup_dir)
        return backup_dir

    except subprocess.TimeoutExpired as exc:
        logger.error("MongoDB backup timed out.")
        raise MongoBackupError("MongoDB backup exceeded the time limit.") from exc

    except OSError as exc:
        logger.error("Unable to execute mongodump.")
        raise MongoBackupError("Unable to execute mongodump.") from exc

    except MongoBackupError:
        raise

    except Exception as exc:
        logger.exception("Unexpected MongoDB backup failure.")
        raise MongoBackupError("Unexpected MongoDB backup failure.") from exc
