"""Sparse retrieval using BM25 lexical matching."""
from typing import List, Optional
from pathlib import Path

from app.ingestion.indexing.bm25_indexer import BM25Indexer
from app.core.models.retrieval import RetrievedChunk, RetrieverType
from app.core.models.filters import RetrievalFilters


class SparseRetriever:
    """
    Sparse (lexical) retrieval using BM25.
    Wraps BM25Indexer and returns RetrievedChunk objects.
    """

    def __init__(
        self,
        bm25_indexer: Optional[BM25Indexer] = None,
        top_k: int = 10,
        cache_path: Optional[Path] = None,
    ):
        self.top_k = top_k
        if bm25_indexer is not None:
            self.indexer = bm25_indexer
        else:
            self.indexer = BM25Indexer(cache_path=cache_path)
            if not self.indexer.load():
                print("Warning: BM25 index not loaded. Call indexer.index_documents() first.")

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[RetrievalFilters] = None,
        acl: Optional[object] = None,
    ) -> List[RetrievedChunk]:
        k = top_k or self.top_k
        processed_query = query.strip().lower()
        raw_results = self.indexer.search(processed_query, top_k=k)

        chunks = []
        for r in raw_results:
            chunk = RetrievedChunk(
                chunk_id=r["chunk_id"],
                content=r["content"],
                metadata=r.get("payload", {}),
                score_breakdown={"sparse": r["score"]},
                retrieval_sources=[RetrieverType.SPARSE],
                acl_users=r.get("payload", {}).get("acl_users", []),
                acl_groups=r.get("payload", {}).get("acl_groups", []),
                acl_roles=r.get("payload", {}).get("acl_roles", []),
            )
            chunks.append(chunk)
        return chunks