"""Dense retrieval using BGE embeddings and Qdrant vector search."""
from typing import List, Optional
from app.ingestion.embeddings.bge_embedder import BGEEmbedder
from app.ingestion.indexing.vector_indexer import VectorIndexer
from app.core.models.retrieval import RetrievedChunk, RetrieverType
from app.core.models.filters import RetrievalFilters
from app.core.models.security import ACLContext
from app.retrieval.filter_builders.qdrant_filter_builder import QdrantFilterBuilder


class DenseRetriever:
    """
    Dense retrieval: embed query → vector search → return RetrievedChunk objects.
    """

    def __init__(
        self,
        embedder: Optional[BGEEmbedder] = None,
        vector_indexer: Optional[VectorIndexer] = None,
        top_k: int = 10,
    ):
        self.embedder = embedder or BGEEmbedder()
        self.vector_indexer = vector_indexer or VectorIndexer()
        self.top_k = top_k

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[RetrievalFilters] = None,
        acl: Optional[ACLContext] = None,
    ) -> List[RetrievedChunk]:
        k = top_k or self.top_k
        query_embedding = self.embedder.encode_single_text(query)
        qdrant_filters = QdrantFilterBuilder.build(filters, acl)
        results = self.vector_indexer.search(query_embedding, top_k=k, filters=qdrant_filters)

        chunks = []
        for r in results:
            chunk = RetrievedChunk(
                chunk_id=r["chunk_id"],
                content=r["content"],
                document_id=r["payload"].get("document_id"),
                source_uri=r["payload"].get("source_uri"),
                page_number=r["payload"].get("page_number"),
                metadata=r["payload"].get("metadata", {}),
                score_breakdown={"dense": r["score"]},
                retrieval_sources=[RetrieverType.DENSE],
                acl_users=r["payload"].get("acl_users", []),
                acl_groups=r["payload"].get("acl_groups", []),
                acl_roles=r["payload"].get("acl_roles", []),
            )
            chunks.append(chunk)
        return chunks