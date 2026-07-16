"""Embedding service for RAG and semantic search."""
from typing import List, Optional
import httpx
import json
from sqlalchemy import text

from app.core.config import settings


class EmbeddingService:
    """Generates embeddings for text using OpenRouter or local models."""

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model = "openai/text-embedding-3-small"

    async def embed(self, text: str) -> str:
        """Generate embedding vector and return as pgvector-compatible string."""
        if not self.api_key:
            # Fallback: return a mock embedding for development
            return self._mock_embedding()

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "input": text[:8000],  # Truncate to fit context
                },
            )

            if response.status_code != 200:
                raise Exception(f"Embedding failed: {response.text}")

            data = response.json()
            embedding = data["data"][0]["embedding"]
            return "[" + ",".join(str(x) for x in embedding) + "]"

    async def embed_batch(self, texts: List[str]) -> List[str]:
        """Generate embeddings for multiple texts."""
        if not self.api_key:
            return [self._mock_embedding() for _ in texts]

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "input": [t[:8000] for t in texts],
                },
            )

            if response.status_code != 200:
                raise Exception(f"Batch embedding failed: {response.text}")

            data = response.json()
            return [
                "[" + ",".join(str(x) for x in item["embedding"]) + "]"
                for item in data["data"]
            ]

    def _mock_embedding(self) -> str:
        """Generate a zero vector for development without API key."""
        dim = settings.EMBEDDING_DIMENSION
        return "[" + ",".join("0.0" for _ in range(dim)) + "]"


class RAGService:
    """Retrieval Augmented Generation - query documents and knowledge."""

    def __init__(self, db_session):
        self.db = db_session
        self.embeddings = EmbeddingService()

    async def query_knowledge(
        self,
        brain_id,
        query: str,
        limit: int = 5,
        threshold: float = 0.7,
    ) -> List[dict]:
        """Search through all knowledge base documents."""
        query_embedding = await self.embeddings.embed(query)

        sql = """
            SELECT d.title, dc.content, d.content_type, dc.chunk_index,
                   1 - (dc.embedding <=> :query::vector) as similarity
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE dc.brain_id = :brain_id
            AND 1 - (dc.embedding <=> :query::vector) > :threshold
            ORDER BY similarity DESC
            LIMIT :limit
        """
        result = await self.db.execute(
            text(sql),
            {
                "query": query_embedding,
                "brain_id": brain_id,
                "threshold": threshold,
                "limit": limit,
            },
        )

        rows = result.fetchall()
        return [
            {
                "title": row[0],
                "content": row[1],
                "type": row[2],
                "similarity": float(row[4]),
            }
            for row in rows
        ]

    async def generate_context_prompt(
        self, brain_id, query: str, max_tokens: int = 4000
    ) -> str:
        """Build a context string from relevant knowledge for LLM prompting."""
        results = await self.query_knowledge(brain_id, query, limit=5)
        if not results:
            return ""

        parts = ["Relevant knowledge from your brain's knowledge base:"]
        for r in results:
            parts.append(f"\n## From: {r['title']} (relevance: {r['similarity']:.2f})")
            parts.append(r["content"][:max_tokens // len(results)])

        return "\n\n".join(parts)
