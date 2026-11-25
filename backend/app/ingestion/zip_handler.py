import zipfile
from pathlib import Path

from app.core.security import safe_join


MAX_ZIP_SIZE = 50 * 1024 * 1024       # 50 MB upload cap
MAX_UNCOMPRESSED = 500 * 1024 * 1024  # 500 MB extracted cap (zip-bomb guard)


def validate_zip(zip_path: Path) -> None:
    if not zip_path.exists():
        raise ValueError("ZIP file does not exist")
    if zip_path.stat().st_size > MAX_ZIP_SIZE:
        raise ValueError(f"ZIP exceeds {MAX_ZIP_SIZE // (1024*1024)} MB limit")
    if not zipfile.is_zipfile(zip_path):
        raise ValueError("Not a valid ZIP file")

    with zipfile.ZipFile(zip_path) as zf:
        total = sum(info.file_size for info in zf.infolist())
        if total > MAX_UNCOMPRESSED:
            raise ValueError(
                f"ZIP would expand to {total // (1024*1024)} MB, "
                f"exceeds {MAX_UNCOMPRESSED // (1024*1024)} MB limit"
            )


def extract_zip(zip_path: Path, dest_dir: Path) -> int:
    """Extract ZIP into dest_dir safely. Returns number of files written."""
    validate_zip(zip_path)
    dest_dir = dest_dir.resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            target = safe_join(dest_dir, info.filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(target, "wb") as dst:
                dst.write(src.read())
            written += 1
    return written