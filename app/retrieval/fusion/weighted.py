"""Weighted fusion: combine dense and sparse scores with intent‑aware weights."""
from typing import List, Optional
from dataclasses import dataclass, field
from app.core.models.retrieval import RetrievedChunk
from app.retrieval.query_understanding.intent_classifier import QueryIntent


@dataclass
class WeightedFusionConfig:
    """Configuration for weighted fusion."""
    normalize: bool = True
    normalization_method: str = "minmax"  # future: "zscore", "rank", "softmax"
    semantic_dense_weight: float = 0.7
    semantic_sparse_weight: float = 0.3


class WeightedFusion:
    """
    Weighted combination of dense and sparse scores.
    Supports intent‑aware weights and score normalisation.
    Returns copied chunks (no in-place mutation).
    """

    INTENT_WEIGHTS = {
        QueryIntent.KEYWORD: (0.3, 0.7), #sparse
        QueryIntent.SEMANTIC: (0.7, 0.3), #dense
        QueryIntent.FACTUAL: (0.6, 0.4), # factual 
        QueryIntent.NAVIGATIONAL: (0.4, 0.6),
    }
    DEFAULT_WEIGHTS = (0.5, 0.5)

    def __init__(self, config: Optional[WeightedFusionConfig] = None):
        self.config = config or WeightedFusionConfig()
        self.normalize = self.config.normalize

    def fuse(
        self,
        dense_chunks: List[RetrievedChunk],
        sparse_chunks: List[RetrievedChunk],
        intent: Optional[QueryIntent] = None,
        top_k: Optional[int] = None,
    ) -> List[RetrievedChunk]:
        # Select weights based on intent
        if intent and intent in self.INTENT_WEIGHTS:
            dw, sw = self.INTENT_WEIGHTS[intent]
        else:
            dw, sw = self.DEFAULT_WEIGHTS

        # Merge chunks by chunk_id
        chunk_map = {}
        for c in dense_chunks:
            chunk_map[c.chunk_id] = self._copy_chunk(c)
        for c in sparse_chunks:
            if c.chunk_id in chunk_map:
                existing = chunk_map[c.chunk_id]
                if "dense" not in existing.score_breakdown and "dense" in c.score_breakdown:
                    existing.score_breakdown["dense"] = c.score_breakdown["dense"]
                if "sparse" not in existing.score_breakdown and "sparse" in c.score_breakdown:
                    existing.score_breakdown["sparse"] = c.score_breakdown["sparse"]
                for src in c.retrieval_sources:
                    if src not in existing.retrieval_sources:
                        existing.retrieval_sources.append(src)
                existing.retrieval_provenance.extend(c.retrieval_provenance)
            else:
                chunk_map[c.chunk_id] = self._copy_chunk(c)

        # Normalise if needed
        if self.normalize:
            self._normalize_scores(list(chunk_map.values()))

        # Compute weighted score
        for c in chunk_map.values():
            d = c.score_breakdown.get("dense_norm" if self.normalize else "dense", 0.0)
            s = c.score_breakdown.get("sparse_norm" if self.normalize else "sparse", 0.0)
            c.score_breakdown["weighted"] = dw * d + sw * s
            c.debug["fusion"] = {
                "method": "weighted",
                "dense_weight": dw,
                "sparse_weight": sw,
                "normalized": self.normalize,
            }

        fused = sorted(chunk_map.values(), key=lambda x: x.score_breakdown.get("weighted", 0.0), reverse=True)
        if top_k is not None:
            fused = fused[:top_k]
        return fused

    def _copy_chunk(self, chunk: RetrievedChunk) -> RetrievedChunk:
        return RetrievedChunk(
            chunk_id=chunk.chunk_id,
            content=chunk.content,
            document_id=chunk.document_id,
            source_uri=chunk.source_uri,
            page_number=chunk.page_number,
            chunk_position=chunk.chunk_position,
            embedding_id=chunk.embedding_id,
            score_breakdown=chunk.score_breakdown.copy(),
            metadata=chunk.metadata.copy(),
            retrieval_provenance=chunk.retrieval_provenance.copy(),
            retrieval_sources=chunk.retrieval_sources.copy(),
            final_rank=chunk.final_rank,
            debug=chunk.debug.copy(),
            retrieved_at=chunk.retrieved_at,
            acl_users=chunk.acl_users,
            acl_groups=chunk.acl_groups,
            acl_roles=chunk.acl_roles,
        )

    def _normalize_scores(self, chunks: List[RetrievedChunk]) -> None:
        dense_scores = [c.score_breakdown.get("dense", 0.0) for c in chunks]
        sparse_scores = [c.score_breakdown.get("sparse", 0.0) for c in chunks]
        min_dense, max_dense = min(dense_scores), max(dense_scores)
        min_sparse, max_sparse = min(sparse_scores), max(sparse_scores)
        for c in chunks:
            d = c.score_breakdown.get("dense", 0.0)
            s = c.score_breakdown.get("sparse", 0.0)
            norm_d = (d - min_dense) / (max_dense - min_dense) if max_dense > min_dense else 0.0
            norm_s = (s - min_sparse) / (max_sparse - min_sparse) if max_sparse > min_sparse else 0.0
            c.score_breakdown["dense_norm"] = norm_d
            c.score_breakdown["sparse_norm"] = norm_s