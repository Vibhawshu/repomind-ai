import os
import re
from pathlib import Path

from app.config import settings


def safe_join(base: Path, untrusted_path: str) -> Path:
    """Join base + untrusted_path, refusing any escape outside base."""
    base = base.resolve()
    target = (base / untrusted_path).resolve()
    if not str(target).startswith(str(base) + os.sep) and target != base:
        raise ValueError(f"Path escapes base directory: {untrusted_path}")
    return target


def sanitize_repo_id(repo_id: str) -> str:
    """Allow only alphanum, underscore, hyphen. Reject path separators."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", repo_id):
        raise ValueError(f"Invalid repo id: {repo_id!r}")
    return repo_id


def repo_dir(repo_id: str) -> Path:
    """Return the on-disk directory for a repo, creating it if needed."""
    repo_id = sanitize_repo_id(repo_id)
    base = settings.storage_path
    target = base / repo_id
    target.mkdir(parents=True, exist_ok=True)
    return target