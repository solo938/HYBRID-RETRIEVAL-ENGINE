"""Production query rewriting with structured metadata, phrase detection, and multiple rewrite modes."""
import re
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict

from app.core.models.retrieval import QueryRewriteResult


class QueryRewriter:
    """
    Advanced query rewriter with:
    - Normalisation
    - Acronym expansion (preserve original)
    - Phrase detection (multi‑word expressions)
    - Synonym expansion
    - Deduplication (order‑preserving)
    - Rewrite modes: dense / sparse / hybrid
    - Placeholder for entity extraction (NER)
    """

    # Acronyms (acronym -> full form)
    ACRONYMS: Dict[str, str] = {
        "rag": "retrieval augmented generation",
        "llm": "large language model",
        "acl": "access control list",
        "bm25": "okapi bm25",
        "ann": "approximate nearest neighbor",
        "hnsw": "hierarchical navigable small world",
        "rrf": "reciprocal rank fusion",
    }

    # Known phrases (preserve as whole units)
    PHRASES: List[str] = [
        "vector database",
        "large language model",
        "retrieval augmented generation",
        "access control",
        "prompt injection",
        "hybrid search",
        "dense retrieval",
        "sparse retrieval",
        "cross encoder",
    ]

    # Synonym expansions (term -> list of synonyms)
    SYNONYMS: Dict[str, List[str]] = {
        "auth": ["authentication", "authorization"],
        "docs": ["documents", "documentation"],
        "api": ["application programming interface"],
        "search": ["retrieval", "information retrieval"],
        "embedding": ["vector", "dense representation"],
    }

    def __init__(
        self,
        mode: str = "hybrid",          # "dense", "sparse", "hybrid"
        expand_acronyms: bool = True,
        expand_synonyms: bool = True,
        detect_phrases: bool = True,
        deduplicate: bool = True,
    ):
        """
        Args:
            mode: "dense" (semantic expansions), "sparse" (lexical expansions), "hybrid" (both)
            expand_acronyms: replace known acronyms with full forms
            expand_synonyms: add synonym variants
            detect_phrases: preserve multi‑word phrases
            deduplicate: remove duplicate tokens while preserving order
        """
        self.mode = mode
        self.expand_acronyms = expand_acronyms
        self.expand_synonyms = expand_synonyms
        self.detect_phrases = detect_phrases
        self.deduplicate = deduplicate

    def rewrite(self, query: str) -> QueryRewriteResult:
        """
        Main entry point: apply all enabled rules and return structured result.
        """
        result = QueryRewriteResult(original_query=query)

        # 1. Normalisation
        normalized = self._normalize(query)
        result.normalized_query = normalized
        result.applied_rules.append("normalization")

        # 2. Phrase detection (before tokenisation)
        if self.detect_phrases:
            phrases = self._detect_phrases(normalized)
            result.detected_phrases = phrases
            if phrases:
                result.applied_rules.append("phrase_detection")

        # 3. Tokenise while preserving phrases
        tokens = self._tokenize_keeping_phrases(normalized)

        # 4. Acronym expansion (full form + keep original)
        if self.expand_acronyms:
            tokens, detected = self._expand_acronyms(tokens)
            result.detected_acronyms.update(detected)
            if detected:
                result.applied_rules.append("acronym_expansion")

        # 5. Synonym expansion
        if self.expand_synonyms:
            tokens, expanded = self._expand_synonyms(tokens)
            result.expanded_terms.update(expanded)
            if expanded:
                result.applied_rules.append("synonym_expansion")

        # 6. Entity extraction (placeholder – to be implemented with spaCy later)
        # entities = self._detect_entities(normalized)
        # result.detected_entities = entities

        # 7. Mode‑specific filtering (dense vs sparse)
        tokens = self._apply_mode_filter(tokens)

        # 8. Deduplication
        if self.deduplicate:
            tokens = self._deduplicate_preserve_order(tokens)

        # 9. Reconstruct final query string
        result.rewritten_query = " ".join(tokens)
        return result

    # --------------------------------------------------------------------------
    # Core methods
    # --------------------------------------------------------------------------

    def _normalize(self, text: str) -> str:
        """Lowercase, strip, collapse whitespace, remove punctuation."""
        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)          # multiple spaces -> one
        text = re.sub(r"[^\w\s]", " ", text)      # punctuation -> space
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _detect_phrases(self, text: str) -> List[str]:
        """Find known multi‑word phrases in the text."""
        found = []
        for phrase in self.PHRASES:
            if phrase in text:
                found.append(phrase)
        return found

    def _tokenize_keeping_phrases(self, text: str) -> List[str]:
        """
        Tokenise while preserving detected phrases as single tokens.
        Replace phrase spaces with underscores, tokenise, then restore.
        """
        for phrase in sorted(self.PHRASES, key=len, reverse=True):
            if phrase in text:
                placeholder = phrase.replace(" ", "_")
                text = text.replace(phrase, placeholder)
        tokens = text.split()
        restored = []
        for t in tokens:
            if "_" in t and t.replace("_", " ") in self.PHRASES:
                restored.append(t.replace("_", " "))
            else:
                restored.append(t)
        return restored

    def _expand_acronyms(self, tokens: List[str]) -> Tuple[List[str], Dict[str, str]]:
        """Add full form after each acronym token. Keep original."""
        expanded = []
        detected = {}
        for t in tokens:
            expanded.append(t)
            if t in self.ACRONYMS:
                full = self.ACRONYMS[t]
                expanded.append(full)
                detected[t] = full
        return expanded, detected

    def _expand_synonyms(self, tokens: List[str]) -> Tuple[List[str], Dict[str, List[str]]]:
        """Add synonyms after the original token."""
        expanded = []
        added = {}
        for t in tokens:
            expanded.append(t)
            if t in self.SYNONYMS:
                syns = self.SYNONYMS[t]
                for syn in syns:
                    if syn not in expanded:
                        expanded.append(syn)
                added[t] = syns
        return expanded, added

    def _apply_mode_filter(self, tokens: List[str]) -> List[str]:
        """Different rewrite strategies for dense vs sparse retrieval."""
        if self.mode == "dense":
            # Dense: keep semantic expansions, remove exact repeated acronyms? (simplify)
            # For now, identity.
            pass
        elif self.mode == "sparse":
            # Sparse: keep acronym full forms, but maybe remove stopwords? Not implemented.
            pass
        # Hybrid: keep everything
        return tokens

    @staticmethod
    def _deduplicate_preserve_order(items: List[str]) -> List[str]:
        """Remove duplicates while preserving first occurrence order."""
        return list(OrderedDict.fromkeys(items))

    # Placeholder for future NER
    def _detect_entities(self, text: str) -> List[str]:
        """To be implemented with spaCy / GLiNER later."""
        return []


# Quick test
if __name__ == "__main__":
    rewriter = QueryRewriter(mode="hybrid")
    queries = [
        "What is RAG and how does it use LLM?",
        "vector database vs bm25 for hybrid search",
    ]
    for q in queries:
        res = rewriter.rewrite(q)
        print(f"\nOriginal: {res.original_query}")
        print(f"Normalized: {res.normalized_query}")
        print(f"Rewritten: {res.rewritten_query}")
        print(f"Detected acronyms: {res.detected_acronyms}")
        print(f"Detected phrases: {res.detected_phrases}")
        print(f"Applied rules: {res.applied_rules}")