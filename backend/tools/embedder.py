"""Text embedding for pgvector retrieval. Defaults to a local, free Ollama
embedding model; set embedding_model to an OpenAI model + openai_api_key to
opt into the paid embeddings API."""

import litellm

from backend.core.config import get_settings


def _chunk(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return [c for c in chunks if c.strip()]


async def embed_document(text: str) -> list[tuple[str, list[float]]]:
    """Chunks `text` and returns (chunk, embedding) pairs."""
    settings = get_settings()
    chunks = _chunk(text)
    if not chunks:
        return []

    response = await litellm.aembedding(
        model=settings.embedding_model,
        input=chunks,
        api_base=settings.ollama_base_url if settings.embedding_model.startswith("ollama/") else None,
    )
    embeddings = [item["embedding"] for item in response["data"]]
    return list(zip(chunks, embeddings, strict=True))


async def embed_query(text: str) -> list[float]:
    settings = get_settings()
    response = await litellm.aembedding(
        model=settings.embedding_model,
        input=[text],
        api_base=settings.ollama_base_url if settings.embedding_model.startswith("ollama/") else None,
    )
    return response["data"][0]["embedding"]
