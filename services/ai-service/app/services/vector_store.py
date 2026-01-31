"""
NEURAXIS - Vector Store Service
Pinecone/Weaviate integration for semantic search
"""

import hashlib
import logging
from datetime import datetime
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.agents.research_schemas import (
    Document,
    DocumentChunk,
    SourceType,
    VectorSearchResult,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Embedding Service
# =============================================================================


class EmbeddingService:
    """
    Generate embeddings using OpenAI text-embedding-3-large.
    """

    MODEL = "text-embedding-3-large"
    DIMENSIONS = 3072  # Full dimensions for highest quality

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self._client = OpenAI(api_key=self.api_key)

        logger.info(f"Embedding service initialized with model: {self.MODEL}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if not text.strip():
            return [0.0] * self.DIMENSIONS

        response = self._client.embeddings.create(
            model=self.MODEL,
            input=text,
            dimensions=self.DIMENSIONS,
        )

        return response.data[0].embedding

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    def embed_batch(self, texts: list[str], batch_size: int = 100) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Maximum batch size

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            # Filter empty texts
            valid_indices = [j for j, t in enumerate(batch) if t.strip()]
            valid_texts = [batch[j] for j in valid_indices]

            if valid_texts:
                response = self._client.embeddings.create(
                    model=self.MODEL,
                    input=valid_texts,
                    dimensions=self.DIMENSIONS,
                )

                # Map embeddings back
                batch_embeddings = [[0.0] * self.DIMENSIONS] * len(batch)
                for idx, j in enumerate(valid_indices):
                    batch_embeddings[j] = response.data[idx].embedding

                all_embeddings.extend(batch_embeddings)
            else:
                all_embeddings.extend([[0.0] * self.DIMENSIONS] * len(batch))

        return all_embeddings


# =============================================================================
# Document Chunking
# =============================================================================


class DocumentChunker:
    """
    Split documents into chunks for vector indexing.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document: Document) -> list[DocumentChunk]:
        """
        Split document into chunks.

        Args:
            document: Document to chunk

        Returns:
            List of DocumentChunk objects
        """
        content = document.content or document.abstract or ""

        if not content:
            return []

        # Simple word-based chunking
        words = content.split()
        chunks = []

        i = 0
        chunk_index = 0

        while i < len(words):
            chunk_words = words[i : i + self.chunk_size]
            chunk_text = " ".join(chunk_words)

            chunk = DocumentChunk(
                id=f"{document.id}:chunk:{chunk_index}",
                document_id=document.id,
                chunk_index=chunk_index,
                content=chunk_text,
                metadata={
                    "source_type": document.source_type.value,
                    "title": document.title,
                    "pmid": document.pmid,
                    "doi": document.doi,
                    "publication_date": document.publication_date.isoformat()
                    if document.publication_date
                    else None,
                    "evidence_grade": document.evidence_grade.value
                    if document.evidence_grade
                    else None,
                },
            )

            chunks.append(chunk)

            i += self.chunk_size - self.chunk_overlap
            chunk_index += 1

        return chunks


# =============================================================================
# Pinecone Vector Store
# =============================================================================


class PineconeStore:
    """
    Pinecone vector store for semantic search.
    """

    def __init__(
        self,
        api_key: str | None = None,
        environment: str | None = None,
        index_name: str = "neuraxis-research",
    ):
        self.api_key = api_key or getattr(settings, "PINECONE_API_KEY", None)
        self.environment = environment or getattr(settings, "PINECONE_ENVIRONMENT", "us-east-1")
        self.index_name = index_name
        self._index = None

        if self.api_key:
            self._init_pinecone()

    def _init_pinecone(self):
        """Initialize Pinecone client and index."""
        try:
            from pinecone import Pinecone, ServerlessSpec

            pc = Pinecone(api_key=self.api_key)

            # Create index if not exists
            if self.index_name not in pc.list_indexes().names():
                pc.create_index(
                    name=self.index_name,
                    dimension=EmbeddingService.DIMENSIONS,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=self.environment,
                    ),
                )
                logger.info(f"Created Pinecone index: {self.index_name}")

            self._index = pc.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")

        except ImportError:
            logger.warning("Pinecone not installed. Vector search disabled.")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")

    async def upsert(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
        namespace: str = "default",
    ) -> int:
        """
        Upsert document chunks to index.

        Args:
            chunks: Document chunks
            embeddings: Corresponding embeddings
            namespace: Pinecone namespace

        Returns:
            Number of vectors upserted
        """
        if not self._index:
            logger.warning("Pinecone not initialized")
            return 0

        vectors = []
        for chunk, embedding in zip(chunks, embeddings):
            vectors.append(
                {
                    "id": chunk.id,
                    "values": embedding,
                    "metadata": {
                        **chunk.metadata,
                        "content": chunk.content[:1000],  # Store truncated content
                    },
                }
            )

        # Upsert in batches
        batch_size = 100
        total_upserted = 0

        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            self._index.upsert(vectors=batch, namespace=namespace)
            total_upserted += len(batch)

        logger.info(f"Upserted {total_upserted} vectors to Pinecone")
        return total_upserted

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        namespace: str = "default",
        filter_dict: dict | None = None,
    ) -> list[VectorSearchResult]:
        """
        Search for similar vectors.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results
            namespace: Pinecone namespace
            filter_dict: Metadata filter

        Returns:
            List of search results
        """
        if not self._index:
            logger.warning("Pinecone not initialized")
            return []

        results = self._index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=namespace,
            filter=filter_dict,
            include_metadata=True,
        )

        search_results = []
        for match in results.matches:
            search_results.append(
                VectorSearchResult(
                    id=match.id,
                    score=match.score,
                    metadata=match.metadata or {},
                    content=match.metadata.get("content") if match.metadata else None,
                )
            )

        return search_results

    async def delete(
        self,
        ids: list[str] | None = None,
        namespace: str = "default",
        delete_all: bool = False,
    ):
        """Delete vectors from index."""
        if not self._index:
            return

        if delete_all:
            self._index.delete(delete_all=True, namespace=namespace)
        elif ids:
            self._index.delete(ids=ids, namespace=namespace)


# =============================================================================
# In-Memory Vector Store (Fallback)
# =============================================================================


class InMemoryVectorStore:
    """
    Simple in-memory vector store for development/testing.
    Uses cosine similarity for search.
    """

    def __init__(self):
        self._vectors: dict[str, dict] = {}
        logger.info("Using in-memory vector store (development mode)")

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    async def upsert(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
        namespace: str = "default",
    ) -> int:
        """Store vectors in memory."""
        for chunk, embedding in zip(chunks, embeddings):
            key = f"{namespace}:{chunk.id}"
            self._vectors[key] = {
                "id": chunk.id,
                "embedding": embedding,
                "metadata": chunk.metadata,
                "content": chunk.content,
            }

        return len(chunks)

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        namespace: str = "default",
        filter_dict: dict | None = None,
    ) -> list[VectorSearchResult]:
        """Search vectors by similarity."""
        results: list[tuple[float, dict]] = []

        for key, data in self._vectors.items():
            if not key.startswith(f"{namespace}:"):
                continue

            # Apply filters
            if filter_dict:
                matches_filter = all(data["metadata"].get(k) == v for k, v in filter_dict.items())
                if not matches_filter:
                    continue

            score = self._cosine_similarity(query_embedding, data["embedding"])
            results.append((score, data))

        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)

        return [
            VectorSearchResult(
                id=data["id"],
                score=score,
                metadata=data["metadata"],
                content=data["content"],
            )
            for score, data in results[:top_k]
        ]

    async def delete(
        self,
        ids: list[str] | None = None,
        namespace: str = "default",
        delete_all: bool = False,
    ):
        """Delete vectors."""
        if delete_all:
            self._vectors = {
                k: v for k, v in self._vectors.items() if not k.startswith(f"{namespace}:")
            }
        elif ids:
            for id in ids:
                key = f"{namespace}:{id}"
                self._vectors.pop(key, None)


# =============================================================================
# Factory
# =============================================================================


def get_vector_store() -> PineconeStore | InMemoryVectorStore:
    """Get configured vector store."""
    pinecone_key = getattr(settings, "PINECONE_API_KEY", None)

    if pinecone_key:
        return PineconeStore()
    else:
        return InMemoryVectorStore()


def get_embedding_service() -> EmbeddingService:
    """Get embedding service."""
    return EmbeddingService()
