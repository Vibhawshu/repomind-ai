from pathlib import Path

IGNORED_DIRS = {
    "node_modules", ".git", "__pycache__", "venv", ".venv", "env",
    "dist", "build", ".next", ".nuxt", "target", "out", "coverage",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "site-packages",
    ".idea", ".vscode", "bin", "obj", "vendor",
}

IGNORED_EXTENSIONS = {
    # binaries
    ".exe", ".dll", ".so", ".dylib", ".bin", ".o", ".a", ".lib",
    ".pyc", ".pyd", ".class", ".jar", ".war",
    # images
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
    # media
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".mkv", ".webm",
    # archives
    ".zip", ".tar", ".gz", ".rar", ".7z", ".bz2", ".xz",
    # docs / data
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    # locks (huge, low-signal)
    ".lock", ".map",
}

# Languages we actively support for chunking/embedding
SUPPORTED_EXTENSIONS = {
    ".py",
    ".js", ".jsx", ".ts", ".tsx",
    ".java", ".kt", ".kts",
    ".go", ".rs",
    ".c", ".h", ".cpp", ".hpp", ".cc",
    ".cs",
    ".rb", ".php",
    ".swift", ".m", ".mm",
    ".scala",
    ".sh", ".bash", ".ps1",
    ".sql",
    ".html", ".css", ".scss", ".sass", ".less",
    ".vue", ".svelte",
    ".md", ".mdx", ".rst",
    ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf",
    ".json", ".xml",
    ".env.example", ".example",
}

MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB per file


def is_ignored_dir(name: str) -> bool:
    return name in IGNORED_DIRS


def should_include_file(path: Path) -> bool:
    """Decide whether a single file should be indexed."""
    # 1) size check
    try:
        if path.stat().st_size > MAX_FILE_SIZE:
            return False
        if path.stat().st_size == 0:
            return False
    except OSError:
        return False

    # 2) extension check
    ext = path.suffix.lower()
    if ext in IGNORED_EXTENSIONS:
        return False
    if ext not in SUPPORTED_EXTENSIONS:
        return False

    # 3) any parent directory ignored?
    for part in path.parts:
        if is_ignored_dir(part):
            return False

    return True


def discover_files(root: Path):
    """Yield every includable source file under root."""
    root = root.resolve()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if should_include_file(path):
            yield path