"""Hybrid retrieval orchestrator: rewrite → expand → plan → execute → deduplicate → fuse → rerank."""
import time
from typing import List, Optional, Dict
from datetime import datetime, timezone

from app.retrieval.dense_retriever import DenseRetriever
from app.retrieval.sparse_retriever import SparseRetriever
from app.retrieval.fusion.rrf import RRFusion
from app.retrieval.fusion.weighted import WeightedFusion
from app.retrieval.reranking.cross_encoder import CrossEncoderReranker
from app.retrieval.query_understanding.query_rewriter import QueryRewriter
from app.retrieval.query_understanding.multi_query_expander import MultiQueryExpander
from app.retrieval.planning.retrieval_planner import RetrievalPlanner
from app.retrieval.query_understanding.intent_classifier import IntentClassifier, QueryIntent
from app.core.models.security import ACLContext
from app.core.models.filters import RetrievalFilters
from app.security.authorization import AuthorizationFilter
from app.core.models.retrieval import (
    RetrievedChunk,
    RetrievalProvenance,
    HybridRetrievalResult,
    RetrievalExecutionTrace,
    RetrieverType,
    QueryStrategy,
    FusionMethod,
    MultiQueryExpansionResult,
    QueryVariant,
)


class HybridRetriever:
    """
    Orchestrates the complete retrieval pipeline:
    Query → Intent Classification → Rewrite → Multi‑query Expansion → Planning →
    Execution → Deduplication → RRF Fusion → Reranking → ACL Filtering.
    """

    def __init__(
        self,
        dense_retriever: Optional[DenseRetriever] = None,
        sparse_retriever: Optional[SparseRetriever] = None,
        fusion: Optional[RRFusion] = None,
        reranker: Optional[CrossEncoderReranker] = None,
        query_rewriter: Optional[QueryRewriter] = None,
        multi_query_expander: Optional[MultiQueryExpander] = None,
        retrieval_planner: Optional[RetrievalPlanner] = None,
        intent_classifier: Optional[IntentClassifier] = None,
        enable_intent_routing: bool = True,
        enable_multi_query: bool = True,
        fusion_method: FusionMethod = FusionMethod.RRF,
        top_k: int = 10,
        rerank_top_k: Optional[int] = None,
    ):
        # Retriever registry
        self.retrievers = {
            RetrieverType.DENSE: dense_retriever or DenseRetriever(),
            RetrieverType.SPARSE: sparse_retriever or SparseRetriever(),
        }
        self.fusion = fusion or RRFusion()
        self.weighted_fusion = WeightedFusion()
        self.reranker = reranker
        self.query_rewriter = query_rewriter or QueryRewriter()
        self.multi_query_expander = multi_query_expander or MultiQueryExpander()
        self.retrieval_planner = retrieval_planner or RetrievalPlanner()
        self.intent_classifier = intent_classifier or IntentClassifier()
        self.enable_intent_routing = enable_intent_routing
        self.enable_multi_query = enable_multi_query
        self.fusion_method = fusion_method
        self.top_k = top_k
        self.rerank_top_k = rerank_top_k or (top_k * 2)

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        acl_context: Optional[ACLContext] = None,
        filters: Optional[RetrievalFilters] = None,
    ) -> HybridRetrievalResult:
        total_start = time.perf_counter()
        k = top_k or self.top_k

        # 0. Intent classification
        if self.enable_intent_routing:
            intent = self.intent_classifier.classify(query)
        else:
            intent = QueryIntent.SEMANTIC

        effective_rerank_top_k = self.rerank_top_k
        if intent == QueryIntent.KEYWORD:
            effective_rerank_top_k = 0

        # 1. Query rewriting
        rewrite_result = self.query_rewriter.rewrite(query)

        # 2. Multi‑query expansion (if enabled)
        if self.enable_multi_query:
            expansion_result = self.multi_query_expander.expand(rewrite_result.rewritten_query)
        else:
            expansion_result = MultiQueryExpansionResult(
                original_query=rewrite_result.rewritten_query,
                rewrite_result=rewrite_result,
                variants=[QueryVariant(query=rewrite_result.rewritten_query, strategy=QueryStrategy.ORIGINAL, weight=1.0)],
                applied_strategies=[QueryStrategy.ORIGINAL]
            )

        # 3. Build retrieval plan (pass intent)
        plan = self.retrieval_planner.build_plan(expansion_result, intent=intent)

        # 4. Execute all steps in the plan
        all_dense_chunks = []
        all_sparse_chunks = []

        for step in plan.steps:
            retriever = self.retrievers.get(step.retriever)
            if not retriever:
                continue
            results = retriever.retrieve(
                query=step.query,
                top_k=step.top_k,
                filters=filters,
                acl=acl_context,  # sparse retriever will ignore if not implemented
            )
            for rank_idx, r in enumerate(results, start=1):
                r.retrieval_provenance.append(
                    RetrievalProvenance(
                        query=step.query,
                        strategy=step.strategy,
                        retriever=step.retriever,
                        rank=rank_idx,
                        score=r.score_breakdown.get(step.retriever.value),
                        weight=step.weight,
                    )
                )
                if step.retriever == RetrieverType.DENSE:
                    all_dense_chunks.append(r)
                else:
                    all_sparse_chunks.append(r)

        # 5. Deduplicate
        dense_by_id = self._deduplicate_chunks(all_dense_chunks)
        sparse_by_id = self._deduplicate_chunks(all_sparse_chunks)

        # 6. Fusion (RRF or Weighted)
        if self.fusion_method == FusionMethod.WEIGHTED:
            fused_chunks = self.weighted_fusion.fuse(
                list(dense_by_id.values()),
                list(sparse_by_id.values()),
                intent=intent,
                top_k=None,
            )
        else:
            fused_chunks = self.fusion.fuse(
                list(dense_by_id.values()),
                list(sparse_by_id.values())
            )

        # 7. ACL filtering (post‑fusion)
        if acl_context:
            fused_chunks = AuthorizationFilter.filter_chunks(fused_chunks, acl_context)

        # 8. Reranking
        rerank_latency = 0.0
        if self.reranker and effective_rerank_top_k > 0:
            rerank_start = time.perf_counter()
            rerank_input = fused_chunks[:effective_rerank_top_k]
            final_chunks = self.reranker.rerank(query, rerank_input, top_k=k)
            rerank_latency = (time.perf_counter() - rerank_start) * 1000
        else:
            final_chunks = fused_chunks[:k]

        # 9. Final rank and timestamp
        for rank, chunk in enumerate(final_chunks, start=1):
            chunk.final_rank = rank
            chunk.retrieved_at = datetime.now(timezone.utc)

        total_latency = (time.perf_counter() - total_start) * 1000

        # 10. Build trace
        trace = RetrievalExecutionTrace(
            original_query=query,
            rewritten_query=rewrite_result.rewritten_query,
            intent=intent.value,
            variants=expansion_result.variants,
            plan_steps=plan.steps,
            dense_calls=len([s for s in plan.steps if s.retriever == RetrieverType.DENSE]),
            sparse_calls=len([s for s in plan.steps if s.retriever == RetrieverType.SPARSE]),
            fusion_method=self.fusion_method,
            latency_breakdown={
                "total_latency_ms": round(total_latency, 2),
                "rerank_latency_ms": round(rerank_latency, 2),
            },
            total_latency_ms=round(total_latency, 2),
        )

        return HybridRetrievalResult(
            results=final_chunks,
            trace=trace,
            retrieval_time_ms=total_latency,
            fusion_method=self.fusion_method,
        )

    # --------------------------------------------------------------------------
    # Helpers
    # --------------------------------------------------------------------------

    def _deduplicate_chunks(self, chunks: List[RetrievedChunk]) -> Dict[str, RetrievedChunk]:
        seen = {}
        for chunk in chunks:
            if chunk.chunk_id not in seen:
                seen[chunk.chunk_id] = chunk
            else:
                existing = seen[chunk.chunk_id]
                existing.retrieval_provenance.extend(chunk.retrieval_provenance)
                for src in chunk.retrieval_sources:
                    if src not in existing.retrieval_sources:
                        existing.retrieval_sources.append(src)
                for score_type in ["dense", "sparse", "rerank"]:
                    if chunk.score_breakdown.get(score_type) is not None:
                        old = existing.score_breakdown.get(score_type)
                        if old is None or chunk.score_breakdown[score_type] > old:
                            existing.score_breakdown[score_type] = chunk.score_breakdown[score_type]
                existing.retrieval_provenance.sort(key=lambda p: p.rank if p.rank is not None else 999999)
        return seen