"""Retrieval planner: converts query variants into executable retrieval steps."""
from typing import Dict, List, Optional

from app.core.models.retrieval import (
    QueryVariant,
    MultiQueryExpansionResult,
    RetrievalPlan,
    RetrievalPlanStep,
    RetrieverType,
    QueryStrategy,
)
from app.retrieval.query_understanding.intent_classifier import QueryIntent


class RetrievalPlanner:
    """
    Converts MultiQueryExpansionResult into a RetrievalPlan.
    Uses strategy‑based routing rules and intent to decide which retriever to use.
    """

    DEFAULT_TOPK_DENSE = 20
    DEFAULT_TOPK_SPARSE = 20

    # Base routing rules: for each strategy, which retrievers to use.
    BASE_ROUTING_RULES: Dict[QueryStrategy, List[RetrieverType]] = {
        QueryStrategy.ORIGINAL: [RetrieverType.DENSE, RetrieverType.SPARSE],
        QueryStrategy.ACRONYM_EXPANSION: [RetrieverType.DENSE, RetrieverType.SPARSE],
        QueryStrategy.SEMANTIC_EXPANSION: [RetrieverType.DENSE],
        QueryStrategy.LEXICAL_EXPANSION: [RetrieverType.SPARSE],
        QueryStrategy.PHRASE_PRESERVED: [RetrieverType.SPARSE],
    }

    # Intent-specific overrides (add or remove retrievers)
    INTENT_ROUTING_OVERRIDES: Dict[QueryIntent, Dict[QueryStrategy, List[RetrieverType]]] = {
        QueryIntent.KEYWORD: {
            # For keyword intent, give lexical strategies higher priority
            QueryStrategy.ORIGINAL: [RetrieverType.SPARSE],          # sparse only
            QueryStrategy.ACRONYM_EXPANSION: [RetrieverType.SPARSE],
            QueryStrategy.LEXICAL_EXPANSION: [RetrieverType.SPARSE],
            QueryStrategy.PHRASE_PRESERVED: [RetrieverType.SPARSE],
            # semantic expansion remains dense only
            QueryStrategy.SEMANTIC_EXPANSION: [RetrieverType.DENSE],
        },
        QueryIntent.SEMANTIC: {
            # For semantic intent, keep both for original and acronym, but boost dense
            # (we can adjust weights later, not retriever list)
            # No changes to base rules for semantic – keep as is.
        },
        # Add more intents as needed
    }

    def __init__(self, dense_top_k: int = DEFAULT_TOPK_DENSE, sparse_top_k: int = DEFAULT_TOPK_SPARSE):
        self.dense_top_k = dense_top_k
        self.sparse_top_k = sparse_top_k

    def build_plan(
        self,
        expansion_result: MultiQueryExpansionResult,
        intent: Optional[QueryIntent] = None,
    ) -> RetrievalPlan:
        """
        Build a retrieval plan from the expanded query result.
        Uses intent (if provided) to override routing rules.
        """
        steps = []
        applied_rules = []

        # Get the effective routing rules (base + intent overrides)
        routing = self._get_routing_rules(intent)

        for variant in expansion_result.variants:
            retrievers = routing.get(variant.strategy, [RetrieverType.DENSE, RetrieverType.SPARSE])
            for retriever in retrievers:
                top_k = self.dense_top_k if retriever == RetrieverType.DENSE else self.sparse_top_k
                step = RetrievalPlanStep(
                    query=variant.query,
                    retriever=retriever,
                    strategy=variant.strategy,
                    top_k=top_k,
                    weight=variant.weight,
                    metadata=variant.metadata,
                )
                steps.append(step)
                applied_rules.append(f"{variant.strategy.value} → {retriever.value}")

        # Deduplicate steps (same query + retriever combination)
        unique_steps = []
        seen = set()
        for step in steps:
            key = (step.query, step.retriever)
            if key not in seen:
                seen.add(key)
                unique_steps.append(step)

        # Deduplicate applied rules while preserving order
        unique_rules = []
        for r in applied_rules:
            if r not in unique_rules:
                unique_rules.append(r)

        return RetrievalPlan(
            original_query=expansion_result.original_query,
            steps=unique_steps,
            applied_rules=unique_rules,
        )

    def _get_routing_rules(self, intent: Optional[QueryIntent]) -> Dict[QueryStrategy, List[RetrieverType]]:
        """Return routing rules with intent‑specific overrides applied."""
        if intent is None or intent not in self.INTENT_ROUTING_OVERRIDES:
            return self.BASE_ROUTING_RULES.copy()

        overrides = self.INTENT_ROUTING_OVERRIDES[intent]
        # Start with base rules, then override per strategy
        rules = self.BASE_ROUTING_RULES.copy()
        for strategy, retrievers in overrides.items():
            rules[strategy] = retrievers
        return rules


# Example usage
if __name__ == "__main__":
    from app.retrieval.query_understanding.multi_query_expander import MultiQueryExpander

    expander = MultiQueryExpander()
    planner = RetrievalPlanner(dense_top_k=15, sparse_top_k=30)

    result = expander.expand("What is RAG and vector database?")
    # Test with different intents
    for intent in [QueryIntent.KEYWORD, QueryIntent.SEMANTIC]:
        plan = planner.build_plan(result, intent=intent)
        print(f"\nIntent: {intent.value}")
        print(f"Original: {plan.original_query}")
        print(f"Applied rules: {plan.applied_rules}")
        for step in plan.steps:
            print(f"  [{step.retriever.value}] weight={step.weight} top_k={step.top_k}: {step.query[:60]}")