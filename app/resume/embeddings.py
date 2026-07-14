"""
Local embeddings — deliberately not calling any LLM provider's embedding API.
Chosen so embedding generation (which happens often: every resume version,
every job posting, every match) never competes with LLM calls for Gemini/Groq
rate limits, and works fully offline.

Model is loaded lazily and cached at module level — loading it is the
expensive part (downloads ~90MB on first run), encoding is cheap.
"""
from functools import lru_cache

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # 384-dim, fast, good enough for resume/JD matching
EMBEDDING_DIM = 384


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Returns one vector per input text, same order."""
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(texts, convert_to_numpy=True)
    return [v.tolist() for v in vectors]


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
