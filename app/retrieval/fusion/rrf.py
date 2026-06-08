"""Reciprocal Rank Fusion (RRF) for combining dense and sparse retrieval results."""
from typing import List, Dict, Any
from collections import defaultdict

from app.core.models.retrieval import RetrievedChunk, RetrieverType


def reciprocal_rank_fusion(
    dense_results: List[RetrievedChunk],
    sparse_results: List[RetrievedChunk],
    k: int = 60,
) -> List[RetrievedChunk]:
    """
    Fuse two lists of RetrievedChunk using RRF.
    Returns a new list of RetrievedChunk sorted by RRF score.
    """
    rrf_scores = defaultdict(float)
    chunk_map = {}

    # Process dense chunks
    for rank, chunk in enumerate(dense_results, start=1):
        chunk_id = chunk.chunk_id  # Use attribute, not subscript
        rrf_scores[chunk_id] += 1.0 / (k + rank)
        if chunk_id not in chunk_map:
            # Make a copy to avoid mutating original
            chunk_map[chunk_id] = RetrievedChunk(
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                document_id=chunk.document_id,
                source_uri=chunk.source_uri,
                page_number=chunk.page_number,
                metadata=chunk.metadata.copy(),
                score_breakdown=chunk.score_breakdown.copy(),
                retrieval_provenance=chunk.retrieval_provenance.copy(),
                retrieval_sources=chunk.retrieval_sources.copy(),
            )
        else:
            existing = chunk_map[chunk_id]
            existing.score_breakdown["dense"] = chunk.score_breakdown.get("dense")

    # Process sparse chunks
    for rank, chunk in enumerate(sparse_results, start=1):
        chunk_id = chunk.chunk_id  # Use attribute, not subscript
        rrf_scores[chunk_id] += 1.0 / (k + rank)
        if chunk_id not in chunk_map:
            chunk_map[chunk_id] = RetrievedChunk(
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                document_id=chunk.document_id,
                source_uri=chunk.source_uri,
                page_number=chunk.page_number,
                metadata=chunk.metadata.copy(),
                score_breakdown=chunk.score_breakdown.copy(),
                retrieval_provenance=chunk.retrieval_provenance.copy(),
                retrieval_sources=chunk.retrieval_sources.copy(),
            )
        else:
            existing = chunk_map[chunk_id]
            existing.score_breakdown["sparse"] = chunk.score_breakdown.get("sparse")

    # Build sorted list
    sorted_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    fused = []
    for chunk_id, rrf_score in sorted_ids:
        chunk = chunk_map[chunk_id]
        chunk.score_breakdown["rrf"] = rrf_score
        fused.append(chunk)

    return fused


class RRFusion:
    def __init__(self, k: int = 60):
        self.k = k

    def fuse(self, dense_results: List[RetrievedChunk], sparse_results: List[RetrievedChunk]) -> List[RetrievedChunk]:
        return reciprocal_rank_fusion(dense_results, sparse_results, self.k)