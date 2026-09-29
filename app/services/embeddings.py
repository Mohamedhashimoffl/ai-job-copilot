from google.genai import types
from app.core.gemini_client import client


def get_embeddings(
    texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT"
) -> list[list[float]]:
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts,
        config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=768),
    )
    return [e.values for e in result.embeddings]


def get_embedding(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
    return get_embeddings([text], task_type)[0]
