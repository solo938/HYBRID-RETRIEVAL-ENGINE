"""Context window models for LLM input."""
from dataclasses import dataclass, field
from typing import List

from app.core.models.retrieval import RetrievedChunk


@dataclass
class ContextWindow:
    """Prepared context for LLM generation."""
    chunks: List[RetrievedChunk]
    total_tokens: int
    truncated: bool = False
    original_chunk_count: int = 0