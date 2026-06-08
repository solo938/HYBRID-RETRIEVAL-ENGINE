"""Assemble retrieval chunks into a token‑bounded, deduplicated context window."""
from typing import List
from app.core.models.retrieval import RetrievedChunk
from app.generation.models.context import ContextWindow
from app.generation.tokenization.token_counter import TokenCounter


class ContextAssembler:
    """Prepare context for LLM generation: deduplicate, sort, token budget."""

    def __init__(self, token_counter: TokenCounter = None, max_tokens: int = 6000):
        self.token_counter = token_counter or TokenCounter()
        self.max_tokens = max_tokens

    def assemble(self, chunks: List[RetrievedChunk], max_tokens: int = None) -> ContextWindow:
        if max_tokens is None:
            max_tokens = self.max_tokens

        original_count = len(chunks)

        # 1. Deduplicate by chunk_id
        seen_ids = set()
        unique_chunks = []
        for c in chunks:
            if c.chunk_id not in seen_ids:
                seen_ids.add(c.chunk_id)
                unique_chunks.append(c)

        # 2. Sort by final_rank (or rerank score)
        unique_chunks.sort(key=lambda x: x.final_rank if x.final_rank is not None else 999)

        # 3. Token budgeting
        selected = []
        total_tokens = 0
        for chunk in unique_chunks:
            chunk_tokens = self.token_counter.count(chunk.content)  # Use .content attribute
            if total_tokens + chunk_tokens <= max_tokens:
                selected.append(chunk)
                total_tokens += chunk_tokens
            else:
                break

        truncated = len(selected) < len(unique_chunks)

        return ContextWindow(
            chunks=selected,
            total_tokens=total_tokens,
            truncated=truncated,
            original_chunk_count=original_count,
        )