"""File storage seam (Architektur §7).

``FileStorage`` is an ABC so the concrete backend (local disk now, S3 later) is
swappable via ``Settings``. ``LocalFileStorage`` writes to ``settings.storage_dir``.

Used by the uploads API (Phase 2) and consumable by later phases that need to
persist or read file bytes.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.config import Settings, get_settings


class FileStorage(ABC):
    """Abstract binary storage. Returns an opaque ``storage_path`` on save."""

    @abstractmethod
    def save(self, data: bytes, name: str) -> str:
        """Persist ``data`` under a name derived from ``name``; return a path/key."""

    @abstractmethod
    def load(self, path: str) -> bytes:
        """Return the bytes previously stored under ``path``."""


class LocalFileStorage(FileStorage):
    """Stores files on the local filesystem under a base directory."""

    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, data: bytes, name: str) -> str:
        # Prefix with a UUID so distinct uploads never collide; keep the
        # original filename suffix for readability/content-type hints.
        safe_name = Path(name).name or "upload"
        stored_name = f"{uuid.uuid4().hex}_{safe_name}"
        target = self.base_dir / stored_name
        target.write_bytes(data)
        # Return a path relative to base_dir so the value is portable.
        return stored_name

    def load(self, path: str) -> bytes:
        target = self.base_dir / path
        if not target.is_file():
            raise FileNotFoundError(path)
        return target.read_bytes()


def get_storage(settings: Settings | None = None) -> FileStorage:
    """Select the storage backend from settings (only ``local`` for the MVP)."""
    settings = settings or get_settings()
    return LocalFileStorage(settings.storage_dir)
