"""Unit tests for the MongoDB backup module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from kali.config import Settings
from kali.modules.mongodb.backup import (
    MongoBackupError,
    create_backup,
)


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Create isolated test settings."""
    return Settings(
        _env_file=None,
        PROJECT_NAME="test-project",
        MONGODB_URI="mongodb://localhost:27017/test_db",
        BACKUP_MODE="database",
        DATABASE_NAME="test_db",
        BACKUP_ROOT=tmp_path / "backups",
        RETENTION_DAYS=3,
        BACKUP_INTERVAL_HOURS=6,
    )


def test_missing_mongodump(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise an error when mongodump is unavailable."""
    monkeypatch.setattr(
        "kali.modules.mongodb.backup.shutil.which",
        lambda _: None,
    )

    with pytest.raises(MongoBackupError, match="mongodump was not found"):
        create_backup(settings)


def test_successful_backup(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return the backup directory when mongodump succeeds."""
    monkeypatch.setattr(
        "kali.modules.mongodb.backup.shutil.which",
        lambda _: "mongodump",
    )

    def fake_run(command: list[str], **kwargs: object) -> MagicMock:
        """Simulate mongodump creating a backup file."""
        output_index = next(
            i for i, arg in enumerate(command) if arg.startswith("--out=")
        )
        output_dir = Path(command[output_index].split("=", 1)[1])
        (output_dir / "test_db").mkdir()
        (output_dir / "test_db" / "collection.bson").write_bytes(b"test")

        result = MagicMock()
        result.returncode = 0
        result.stdout = ""
        result.stderr = ""
        return result

    monkeypatch.setattr(
        "kali.modules.mongodb.backup.subprocess.run",
        fake_run,
    )

    result = create_backup(settings)

    assert result.exists()
    assert result.is_dir()
    assert list(result.rglob("*.bson"))


def test_mongodump_failure(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise an error when mongodump returns a non-zero exit code."""
    monkeypatch.setattr(
        "kali.modules.mongodb.backup.shutil.which",
        lambda _: "mongodump",
    )

    result = MagicMock()
    result.returncode = 1
    result.stdout = ""
    result.stderr = "simulated failure"

    monkeypatch.setattr(
        "kali.modules.mongodb.backup.subprocess.run",
        lambda *args, **kwargs: result,
    )

    with pytest.raises(MongoBackupError, match="exit code 1"):
        create_backup(settings)


def test_backup_timeout(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise an error when mongodump exceeds its timeout."""
    monkeypatch.setattr(
        "kali.modules.mongodb.backup.shutil.which",
        lambda _: "mongodump",
    )

    def fake_run(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired("mongodump", 3600)

    monkeypatch.setattr(
        "kali.modules.mongodb.backup.subprocess.run",
        fake_run,
    )

    with pytest.raises(MongoBackupError, match="exceeded the time limit"):
        create_backup(settings)


def test_empty_backup_output(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject a successful command that produces no files."""
    monkeypatch.setattr(
        "kali.modules.mongodb.backup.shutil.which",
        lambda _: "mongodump",
    )

    result = MagicMock()
    result.returncode = 0
    result.stdout = ""
    result.stderr = ""

    monkeypatch.setattr(
        "kali.modules.mongodb.backup.subprocess.run",
        lambda *args, **kwargs: result,
    )

    with pytest.raises(MongoBackupError, match="produced no backup files"):
        create_backup(settings)
