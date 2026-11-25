from app.vectorstore.indexer import search


def retrieve_chunks(repo_id: str, query: str, top_k: int = 5) -> list[dict]:
    """Semantic top-k retrieval scoped to a single repo."""
    return search(repo_id=repo_id, query=query, top_k=top_k)