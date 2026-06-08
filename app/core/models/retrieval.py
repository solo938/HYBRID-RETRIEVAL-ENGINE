"""Canonical retrieval domain models. No raw dicts across retrieval boundaries."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


# ------------------------------------------------------------------------------
# Enums for type safety
# ------------------------------------------------------------------------------

class RetrieverType(str, Enum):
    DENSE = "dense"
    SPARSE = "sparse"
    HYBRID = "hybrid"


class QueryStrategy(str, Enum):
    ORIGINAL = "original"
    ACRONYM_EXPANSION = "acronym_expansion"
    SEMANTIC_EXPANSION = "semantic_expansion"
    LEXICAL_EXPANSION = "lexical_expansion"
    PHRASE_PRESERVED = "phrase_preserved"


class FusionMethod(str, Enum):
    RRF = "rrf"
    WEIGHTED = "weighted"


# ------------------------------------------------------------------------------
# Provenance & tracing
# ------------------------------------------------------------------------------

@dataclass
class RetrievalProvenance:
    """Records which query variant and retriever produced a chunk."""
    query: str
    strategy: QueryStrategy
    retriever: RetrieverType
    rank: Optional[int] = None
    score: Optional[float] = None
    weight: float = 1.0
    latency_ms: Optional[float] = None


@dataclass
class RetrievalExecutionTrace:
    """Full trace of a retrieval execution for observability."""
    original_query: str
    rewritten_query: Optional[str] = None
    intent: Optional[str] = None                     # <-- ADDED
    variants: List['QueryVariant'] = field(default_factory=list)
    plan_steps: List['RetrievalPlanStep'] = field(default_factory=list)
    dense_calls: int = 0
    sparse_calls: int = 0
    fusion_method: FusionMethod = FusionMethod.RRF
    latency_breakdown: Dict[str, float] = field(default_factory=dict)
    total_latency_ms: float = 0.0


# ------------------------------------------------------------------------------
# Core retrieval result
# ------------------------------------------------------------------------------

@dataclass
class RetrievedChunk:
    """The fundamental unit returned by retrieval."""
    chunk_id: str
    content: str
    document_id: Optional[str] = None
    source_uri: Optional[str] = None
    page_number: Optional[int] = None
    chunk_position: Optional[int] = None
    embedding_id: Optional[str] = None
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    retrieval_provenance: List[RetrievalProvenance] = field(default_factory=list)
    retrieval_sources: List[RetrieverType] = field(default_factory=list)
    final_rank: Optional[int] = None
    debug: Dict[str, Any] = field(default_factory=dict)
    retrieved_at: Optional[datetime] = None
    # ACL fields
    acl_users: List[str] = field(default_factory=list)
    acl_groups: List[str] = field(default_factory=list)
    acl_roles: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for APIs, logging, etc."""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "document_id": self.document_id,
            "source_uri": self.source_uri,
            "page_number": self.page_number,
            "chunk_position": self.chunk_position,
            "embedding_id": self.embedding_id,
            "score_breakdown": self.score_breakdown,
            "metadata": self.metadata,
            "retrieval_provenance": [p.__dict__ for p in self.retrieval_provenance],
            "retrieval_sources": [r.value for r in self.retrieval_sources],
            "final_rank": self.final_rank,
            "debug": self.debug,
            "retrieved_at": self.retrieved_at.isoformat() if self.retrieved_at else None,
            "acl_users": self.acl_users,
            "acl_groups": self.acl_groups,
            "acl_roles": self.acl_roles,
        }


# ------------------------------------------------------------------------------
# Query understanding models
# ------------------------------------------------------------------------------

@dataclass
class QueryRewriteResult:
    """Structured output of query rewriting."""
    original_query: str
    normalized_query: str = ""
    rewritten_query: str = ""
    detected_acronyms: Dict[str, str] = field(default_factory=dict)
    expanded_terms: Dict[str, List[str]] = field(default_factory=dict)
    detected_phrases: List[str] = field(default_factory=list)
    detected_entities: List[str] = field(default_factory=list)
    applied_rules: List[str] = field(default_factory=list)


@dataclass
class QueryVariant:
    """A single query variant with its strategy and weight."""
    query: str
    strategy: QueryStrategy
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiQueryExpansionResult:
    """Result of expanding a query into multiple variants."""
    original_query: str
    rewrite_result: QueryRewriteResult
    variants: List[QueryVariant] = field(default_factory=list)
    applied_strategies: List[QueryStrategy] = field(default_factory=list)


# ------------------------------------------------------------------------------
# Planning models
# ------------------------------------------------------------------------------

@dataclass
class RetrievalPlanStep:
    """A single retrieval operation to be executed."""
    query: str
    retriever: RetrieverType
    strategy: QueryStrategy
    top_k: int
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalPlan:
    """Complete plan for executing retrieval from a user query."""
    original_query: str
    steps: List[RetrievalPlanStep]
    applied_rules: List[str] = field(default_factory=list)


# ------------------------------------------------------------------------------
# Final orchestration result
# ------------------------------------------------------------------------------

@dataclass
class HybridRetrievalResult:
    """Final output of the hybrid retrieval pipeline."""
    results: List[RetrievedChunk]
    trace: RetrievalExecutionTrace
    total_results: int = 0
    retrieval_time_ms: float = 0.0
    fusion_method: FusionMethod = FusionMethod.RRF

    def __post_init__(self):
        self.total_results = len(self.results)
