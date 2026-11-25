import uuid

from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from app.embeddings.embedder import embedding_dim, embed_query, embed_texts
from app.processing.chunker import CodeChunk
from app.vectorstore.qdrant_client import get_qdrant


COLLECTION = "code_chunks"


def ensure_collection() -> None:
    client = get_qdrant()
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=embedding_dim(), distance=Distance.COSINE),
        )

    for field in ("repo_id", "file_path"):
        try:
            client.create_payload_index(
                collection_name=COLLECTION,
                field_name=field,
                field_schema=PayloadSchemaType.KEYWORD,
                wait=True,
            )
        except Exception:
            pass


def index_chunks(repo_id: str, chunks: list[CodeChunk]) -> int:
    """Embed and upsert chunks in small batches to prevent memory crashes."""
    if not chunks:
        return 0
    ensure_collection()

    client = get_qdrant()
    total_points = 0
    batch_size = 16  # Process 16 chunks at a time

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c.content for c in batch]
        
        # Generate embeddings for just this small batch
        vectors = embed_texts(texts)

        points = []
        for chunk, vec in zip(batch, vectors):
            payload = chunk.to_metadata()
            payload["repo_id"] = repo_id
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload=payload,
            ))

        client.upsert(collection_name=COLLECTION, points=points, wait=True)
        total_points += len(points)
        print(f"Indexed {total_points}/{len(chunks)} chunks...")

    return total_points


def search(
    repo_id: str,
    query: str,
    top_k: int = 10,
    file_path_contains: str | None = None,
) -> list[dict]:
    ensure_collection()
    qvec = embed_query(query)

    must = [FieldCondition(key="repo_id", match=MatchValue(value=repo_id))]
    if file_path_contains:
        must.append(
            FieldCondition(key="file_path", match=MatchValue(value=file_path_contains))
        )

    client = get_qdrant()
    hits = client.search(
        collection_name=COLLECTION,
        query_vector=qvec,
        query_filter=Filter(must=must),
        limit=top_k,
        with_payload=True,
    )

    return [
        {
            "score": h.score,
            "file_path": h.payload.get("file_path"),
            "start_line": h.payload.get("start_line"),
            "end_line": h.payload.get("end_line"),
            "language": h.payload.get("language"),
            "chunk_type": h.payload.get("chunk_type"),
            "symbol": h.payload.get("symbol"),
            "repo_id": h.payload.get("repo_id"),
            "content": h.payload.get("_content", ""),
        }
        for h in hits
    ]


def delete_repo(repo_id: str) -> int:
    ensure_collection()
    client = get_qdrant()
    flt = Filter(must=[FieldCondition(key="repo_id", match=MatchValue(value=repo_id))])

    try:
        count_before = client.count(collection_name=COLLECTION, count_filter=flt).count
    except Exception:
        count_before = 0

    client.delete(
        collection_name=COLLECTION,
        points_selector=flt,
        wait=True,
    )
    return count_before