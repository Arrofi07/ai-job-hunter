"""
Thin Qdrant wrapper. Generic on purpose — resume chunks today, job posting
chunks in Slice 3/4 use the same interface with a different collection name,
so the matching engine doesn't need two different vector-store clients.
"""
import uuid

from app.config import settings


def _client():
    from qdrant_client import QdrantClient

    return QdrantClient(url=settings.qdrant_url)


def ensure_collection(collection_name: str, vector_size: int) -> None:
    from qdrant_client.models import Distance, VectorParams

    client = _client()
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def upsert_vectors(
    collection_name: str,
    vectors: list[list[float]],
    payloads: list[dict],
) -> list[str]:
    """Upserts vectors with auto-generated point IDs. Returns the generated IDs
    so callers can store them for later deletion/update if needed."""
    from qdrant_client.models import PointStruct

    if len(vectors) != len(payloads):
        raise ValueError("vectors and payloads must be the same length")

    ids = [str(uuid.uuid4()) for _ in vectors]
    points = [
        PointStruct(id=point_id, vector=vector, payload=payload)
        for point_id, vector, payload in zip(ids, vectors, payloads)
    ]
    _client().upsert(collection_name=collection_name, points=points)
    return ids


def delete_by_payload(collection_name: str, key: str, value) -> None:
    """E.g. delete_by_payload('resume_chunks', 'resume_version_id', 3) to clear
    out an old resume version's vectors before/instead of keeping them forever."""
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    _client().delete(
        collection_name=collection_name,
        points_selector=Filter(
            must=[FieldCondition(key=key, match=MatchValue(value=value))]
        ),
    )
