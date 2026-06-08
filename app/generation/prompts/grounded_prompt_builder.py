"""Build grounded prompts with citations."""
from typing import List
from app.core.models.retrieval import RetrievedChunk
from app.generation.models.citations import Citation


class GroundedPromptBuilder:
    """Build prompts that enforce grounded, citation‑aware answers."""

    SYSTEM_PROMPT = """You are an enterprise AI assistant.

RULES:
1. Answer ONLY using the provided context.
2. If the answer cannot be found in the context, say "I don't have enough information to answer that."
3. Cite sources inline using brackets like [1], [2], etc.
4. Do not add information from outside the context.
5. Be concise and accurate."""

    def build(self, query: str, chunks: List[RetrievedChunk], citations: List[Citation]) -> str:
        context_parts = []
        for c in chunks:
            cid = c.metadata.get("citation_id")
            if cid:
                context_parts.append(f"[{cid}] {c.content}")
            else:
                context_parts.append(c.content)

        context = "\n\n".join(context_parts)

        return f"""{self.SYSTEM_PROMPT}

QUESTION:
{query}

CONTEXT:
{context}

ANSWER:"""