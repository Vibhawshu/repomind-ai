from pathlib import Path

from app.core.security import repo_dir


def load_chunk_content(repo_id: str, hit: dict) -> str:
    """Read the actual code for a retrieved chunk from disk.

    Falls back to whatever content was stored in the vector payload (empty
    for now) if the file no longer exists.
    """
    target = repo_dir(repo_id) / hit["file_path"]
    if not target.exists():
        return hit.get("content", "")
    try:
        lines = target.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return hit.get("content", "")
    s = max(1, int(hit["start_line"]))
    e = min(len(lines), int(hit["end_line"]))
    return "\n".join(lines[s - 1:e])


def build_context(repo_id: str, hits: list[dict], max_chars: int = 8000) -> tuple[str, list[dict]]:
    """Return (context_string_for_llm, sources_list_for_ui)."""
    parts: list[str] = []
    sources: list[dict] = []
    used = 0

    for i, hit in enumerate(hits, start=1):
        content = load_chunk_content(repo_id, hit)
        if not content.strip():
            continue

        header = (
            f"[Source {i}] {hit['file_path']} "
            f"(lines {hit['start_line']}-{hit['end_line']}, "
            f"{hit.get('language', '?')}, {hit.get('chunk_type', '?')}"
            f"{', ' + hit['symbol'] if hit.get('symbol') else ''})"
        )
        block = f"{header}\n```\n{content}\n```"

        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)

        sources.append({
            "index": i,
            "file_path": hit["file_path"],
            "start_line": hit["start_line"],
            "end_line": hit["end_line"],
            "language": hit.get("language"),
            "symbol": hit.get("symbol"),
            "score": hit.get("score"),
        })

    return "\n\n".join(parts), sources