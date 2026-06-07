"""
Embedding pipeline – vectorise, store, and search honeypot attacks.

Bridges the :class:`NIMClient` embedding endpoint with a Qdrant
vector store so that the investigation workflow can retrieve
semantically similar past attacks (RAG context).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse

from app.ai.nim_client import NIMClient
from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Default vector size for the NV-EmbedQA-E5 model family
_VECTOR_SIZE: int = 1024


class EmbeddingService:
    """Async embedding pipeline backed by NIM + Qdrant."""

    def __init__(self, nim_client: NIMClient, settings: Settings) -> None:
        self._nim = nim_client
        self._collection = settings.QDRANT_COLLECTION
        self._qdrant = AsyncQdrantClient(url=settings.QDRANT_URL)

        logger.info(
            "embedding_service.initialised",
            qdrant_url=settings.QDRANT_URL,
            collection=self._collection,
        )

    # ── Collection management ────────────────────────────────────────────

    async def ensure_collection(self) -> None:
        """Create the Qdrant collection if it does not already exist.

        Uses cosine distance and a vector size of 1024, matching the
        NV-EmbedQA-E5-v5 output dimensionality.
        """
        try:
            collections = await self._qdrant.get_collections()
            existing = {c.name for c in collections.collections}

            if self._collection in existing:
                logger.debug(
                    "embedding_service.collection_exists",
                    collection=self._collection,
                )
                return

            await self._qdrant.create_collection(
                collection_name=self._collection,
                vectors_config=qmodels.VectorParams(
                    size=_VECTOR_SIZE,
                    distance=qmodels.Distance.COSINE,
                ),
            )

            # Create payload indexes for common filter fields
            for field_name, field_type in [
                ("src_ip", qmodels.PayloadSchemaType.KEYWORD),
                ("country", qmodels.PayloadSchemaType.KEYWORD),
                ("service", qmodels.PayloadSchemaType.KEYWORD),
                ("severity", qmodels.PayloadSchemaType.KEYWORD),
                ("attack_type", qmodels.PayloadSchemaType.KEYWORD),
            ]:
                await self._qdrant.create_payload_index(
                    collection_name=self._collection,
                    field_name=field_name,
                    field_schema=field_type,
                )

            logger.info(
                "embedding_service.collection_created",
                collection=self._collection,
                vector_size=_VECTOR_SIZE,
                distance="cosine",
            )
        except (UnexpectedResponse, Exception) as exc:
            logger.error(
                "embedding_service.collection_error",
                collection=self._collection,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            raise

    # ── Embedding generation ─────────────────────────────────────────────

    async def embed_attack(self, attack_data: dict[str, Any]) -> list[float]:
        """Build a textual representation of an attack and embed it.

        The text template mirrors the fields most useful for semantic
        similarity: service, origin, credentials, commands, and
        threat indicators.

        Args:
            attack_data: Dictionary containing attack event fields.

        Returns:
            A list of floats – the embedding vector.
        """
        text = (
            f"{attack_data.get('service', 'unknown')} attack "
            f"from {attack_data.get('src_ip', 'unknown')} "
            f"({attack_data.get('country', 'unknown')}): "
            f"user={attack_data.get('username', '')} "
            f"pass={attack_data.get('password', '')} "
            f"cmd={attack_data.get('command', '')} "
            f"severity={attack_data.get('severity', 'unknown')} "
            f"threat_score={attack_data.get('threat_score', 0)}"
        )

        embedding = await self._nim.generate_embedding(text)
        logger.debug(
            "embedding_service.attack_embedded",
            src_ip=attack_data.get("src_ip"),
            text_length=len(text),
            vector_dim=len(embedding),
        )
        return embedding

    # ── Vector storage ───────────────────────────────────────────────────

    async def store_attack_vector(
        self,
        attack_id: str,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> None:
        """Upsert an attack embedding into Qdrant with associated metadata.

        Args:
            attack_id: Unique identifier for the attack event (UUID string).
            embedding: The embedding vector to store.
            metadata: Payload fields – should include ``src_ip``,
                ``country``, ``service``, ``severity``, ``attack_type``,
                ``timestamp``, ``reputation``, ``abuse_confidence``, and
                ``threat_score``.
        """
        # Ensure timestamp is serialisable
        payload = dict(metadata)
        if "timestamp" in payload and isinstance(payload["timestamp"], datetime):
            payload["timestamp"] = payload["timestamp"].isoformat()

        try:
            # Convert attack_id to a deterministic UUID for Qdrant
            try:
                point_id = str(uuid.UUID(attack_id))
            except ValueError:
                point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, attack_id))

            await self._qdrant.upsert(
                collection_name=self._collection,
                points=[
                    qmodels.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload,
                    ),
                ],
            )
            logger.info(
                "embedding_service.vector_stored",
                attack_id=attack_id,
                collection=self._collection,
            )
        except (UnexpectedResponse, Exception) as exc:
            logger.error(
                "embedding_service.store_error",
                attack_id=attack_id,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            raise

    # ── Similarity search ────────────────────────────────────────────────

    async def search_similar_attacks(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for attacks similar to *query_embedding* in Qdrant.

        Args:
            query_embedding: The query vector.
            top_k: Maximum number of results to return.
            filters: Optional key-value filters applied to payload fields.
                Example: ``{"service": "ssh", "severity": "critical"}``

        Returns:
            A list of dicts with ``id``, ``score``, and payload fields.
        """
        qdrant_filter: qmodels.Filter | None = None
        if filters:
            conditions = [
                qmodels.FieldCondition(
                    key=key,
                    match=qmodels.MatchValue(value=value),
                )
                for key, value in filters.items()
            ]
            qdrant_filter = qmodels.Filter(must=conditions)

        try:
            results = await self._qdrant.query_points(
                collection_name=self._collection,
                query=query_embedding,
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True,
            )

            hits: list[dict[str, Any]] = []
            for point in results.points:
                hit: dict[str, Any] = {
                    "id": str(point.id),
                    "score": point.score if hasattr(point, "score") else None,
                }
                if point.payload:
                    hit.update(point.payload)
                hits.append(hit)

            logger.info(
                "embedding_service.search_completed",
                top_k=top_k,
                results_count=len(hits),
                has_filters=filters is not None,
            )
            return hits

        except (UnexpectedResponse, Exception) as exc:
            logger.error(
                "embedding_service.search_error",
                error=str(exc),
                error_type=type(exc).__name__,
            )
            return []

    async def search_by_text(
        self,
        text: str,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Embed *text* and search for similar attacks.

        Convenience wrapper around :meth:`generate_embedding` +
        :meth:`search_similar_attacks`.

        Args:
            text: Free-form search query.
            top_k: Maximum number of results.

        Returns:
            A list of matching attack dicts.
        """
        embedding = await self._nim.generate_embedding(text)
        return await self.search_similar_attacks(
            query_embedding=embedding,
            top_k=top_k,
        )

from app.core.config import get_settings
from app.ai.nim_client import nim_client

embedding_service = EmbeddingService(nim_client, get_settings())
