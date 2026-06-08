"""Multi‑query expansion: generate multiple retrieval variants from a single query."""
from typing import Dict, List, Optional
from collections import OrderedDict

from app.core.models.retrieval import (
    QueryRewriteResult,
    QueryVariant,
    MultiQueryExpansionResult,
    QueryStrategy,
)
from .query_rewriter import QueryRewriter


class MultiQueryExpander:
    """
    Expand one query into several retrieval variants to maximise recall.
    Uses the structured QueryRewriteResult to generate strategy‑specific variants.
    """

    def __init__(
        self,
        rewriter: Optional[QueryRewriter] = None,
        include_original: bool = True,
        include_acronym_expansion: bool = True,
        include_lexical_expansion: bool = True,
        include_semantic_expansion: bool = True,
        include_phrase_preserved: bool = True,
        max_variants: int = 5,
    ):
        self.rewriter = rewriter or QueryRewriter(mode="hybrid")
        self.include_original = include_original
        self.include_acronym_expansion = include_acronym_expansion
        self.include_lexical_expansion = include_lexical_expansion
        self.include_semantic_expansion = include_semantic_expansion
        self.include_phrase_preserved = include_phrase_preserved
        self.max_variants = max_variants

    def expand(self, query: str) -> MultiQueryExpansionResult:
        """
        Generate query variants based on enabled strategies.
        Returns a result object with deduplicated variants.
        """
        # Step 1: get structured rewrite result
        rewrite_result = self.rewriter.rewrite(query)

        variants = []
        applied = []

        # Helper to add variant if not already present (by normalized query)
        seen_queries = set()

        def add_variant(q: str, strategy: QueryStrategy, weight: float, extra_meta: Optional[Dict] = None):
            norm_q = q.strip().lower()
            if norm_q in seen_queries:
                return
            seen_queries.add(norm_q)
            meta = extra_meta or {}
            variants.append(QueryVariant(query=q, strategy=strategy, weight=weight, metadata=meta))

        # 1. Original query (raw user input)
        if self.include_original:
            add_variant(query, QueryStrategy.ORIGINAL, 1.0, {"source": "original"})
            applied.append(QueryStrategy.ORIGINAL)

        # 2. Acronym‑expanded (full rewrite result)
        if self.include_acronym_expansion and rewrite_result.rewritten_query != query:
            add_variant(
                rewrite_result.rewritten_query,
                QueryStrategy.ACRONYM_EXPANSION,
                0.95,
                {"detected_acronyms": rewrite_result.detected_acronyms}
            )
            applied.append(QueryStrategy.ACRONYM_EXPANSION)

        # 3. Lexical expansion: heavy keyword/synonym version for BM25
        if self.include_lexical_expansion:
            lexical_tokens = []
            if rewrite_result.expanded_terms:
                for term, syns in rewrite_result.expanded_terms.items():
                    lexical_tokens.append(term)
                    lexical_tokens.extend(syns)
            if rewrite_result.detected_acronyms:
                for acro, full in rewrite_result.detected_acronyms.items():
                    lexical_tokens.append(acro)
                    lexical_tokens.append(full)
            if lexical_tokens:
                orig_tokens = rewrite_result.normalized_query.split()
                all_tokens = list(OrderedDict.fromkeys(orig_tokens + lexical_tokens))
                lexical_query = " ".join(all_tokens)
                if lexical_query != rewrite_result.rewritten_query:
                    add_variant(lexical_query, QueryStrategy.LEXICAL_EXPANSION, 0.8,
                                {"token_count": len(all_tokens)})
                    applied.append(QueryStrategy.LEXICAL_EXPANSION)

        # 4. Semantic expansion: use only the normalized + acronym full forms (no synonyms)
        if self.include_semantic_expansion:
            sem_tokens = rewrite_result.normalized_query.split()
            if rewrite_result.detected_acronyms:
                for full in rewrite_result.detected_acronyms.values():
                    sem_tokens.append(full)
            sem_query = " ".join(OrderedDict.fromkeys(sem_tokens))
            if sem_query not in [v.query for v in variants]:
                add_variant(sem_query, QueryStrategy.SEMANTIC_EXPANSION, 0.9, {"source": "acronyms_only"})
                applied.append(QueryStrategy.SEMANTIC_EXPANSION)

        # 5. Phrase‑preserved variant (emphasise detected phrases)
        if self.include_phrase_preserved and rewrite_result.detected_phrases:
            phrase_query = " ".join(rewrite_result.detected_phrases) + " " + rewrite_result.normalized_query
            if phrase_query != rewrite_result.rewritten_query:
                add_variant(phrase_query, QueryStrategy.PHRASE_PRESERVED, 0.85,
                            {"phrases": rewrite_result.detected_phrases})
                applied.append(QueryStrategy.PHRASE_PRESERVED)

        # Deduplicate and limit
        variants = variants[:self.max_variants]

        return MultiQueryExpansionResult(
            original_query=query,
            rewrite_result=rewrite_result,
            variants=variants,
            applied_strategies=applied,
        )


# Example usage
if __name__ == "__main__":
    expander = MultiQueryExpander()
    query = "What is RAG and how does it use vector database?"
    result = expander.expand(query)

    print(f"Original: {result.original_query}")
    print(f"Strategies used: {[s.value for s in result.applied_strategies]}")
    for v in result.variants:
        print(f"  [{v.strategy.value}] weight={v.weight}: {v.query}")