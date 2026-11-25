import ast
from dataclasses import dataclass, asdict
from pathlib import Path


MAX_LINES_PER_CHUNK = 60
MIN_LINES_PER_CHUNK = 2
MAX_CHUNKS_PER_FILE = 50  # Prevent massive files from crashing the app


@dataclass
class CodeChunk:
    file_path: str
    start_line: int
    end_line: int
    language: str
    chunk_type: str
    symbol: str
    content: str

    def to_metadata(self) -> dict:
        d = asdict(self)
        d.pop("content")
        return d


def _language_from_path(path: Path) -> str:
    return {
        ".py": "python",
        ".js": "javascript", ".jsx": "javascript",
        ".ts": "typescript", ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".c": "c", ".h": "c",
        ".cpp": "cpp", ".hpp": "cpp", ".cc": "cpp",
        ".cs": "csharp",
        ".rb": "ruby",
        ".php": "php",
        ".md": "markdown",
        ".json": "json",
        ".yml": "yaml", ".yaml": "yaml",
        ".sql": "sql",
        ".html": "html",
        ".css": "css", ".scss": "scss",
    }.get(path.suffix.lower(), "unknown")


def _append(out, file_path, lines, start, end, ctype, language, symbol=""):
    if end < start:
        return
    content = "\n".join(lines[start - 1:end])
    if not content.strip():
        return
    out.append(CodeChunk(
        file_path=file_path,
        start_line=start,
        end_line=end,
        language=language,
        chunk_type=ctype,
        symbol=symbol,
        content=content,
    ))


def _chunk_python(file_path: str, source: str) -> list[CodeChunk]:
    lines = source.splitlines()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return _chunk_generic(file_path, source, "python")

    chunks: list[CodeChunk] = []
    covered: list[tuple[int, int]] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno
            end = getattr(node, "end_lineno", start) or start
            if end - start + 1 < MIN_LINES_PER_CHUNK:
                continue
            ctype = "class" if isinstance(node, ast.ClassDef) else "function"
            _append(chunks, file_path, lines, start, end, ctype, "python",
                    getattr(node, "name", ""))
            covered.append((start, end))

    if lines:
        covered.sort()
        cursor = 1
        for s, e in covered:
            if s > cursor:
                _append(chunks, file_path, lines, cursor, s - 1, "module", "python")
            cursor = max(cursor, e + 1)
        if cursor <= len(lines):
            _append(chunks, file_path, lines, cursor, len(lines), "module", "python")

    return chunks


def _chunk_generic(file_path: str, source: str, language: str) -> list[CodeChunk]:
    lines = source.splitlines()
    n = len(lines)
    if n == 0:
        return []
    chunks: list[CodeChunk] = []
    i = 0
    while i < n:
        start = i
        end = min(i + MAX_LINES_PER_CHUNK - 1, n - 1)
        if end < n - 1:
            for j in range(end, max(start + MIN_LINES_PER_CHUNK, end - 20), -1):
                if not lines[j].strip():
                    end = j
                    break
        _append(chunks, file_path, lines, start + 1, end + 1, "block", language)
        i = end + 1
    return chunks


def chunk_file(path: Path, root: Path) -> list[CodeChunk]:
    try:
        # Limit reading to the first 50,000 lines to prevent memory spikes
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[:50000]
        source = "".join(lines)
    except Exception:
        return []

    rel = path.relative_to(root).as_posix()
    language = _language_from_path(path)

    chunks = []
    if language == "python":
        chunks = _chunk_python(rel, source)
    else:
        chunks = _chunk_generic(rel, source, language)

    # Hard limit to prevent OOM crash
    return chunks[:MAX_CHUNKS_PER_FILE]