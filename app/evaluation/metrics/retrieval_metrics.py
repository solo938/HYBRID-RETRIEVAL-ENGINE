"""Standard retrieval metrics: Recall@K, Precision@K, MRR, nDCG."""
import numpy as np
from typing import List, Set, Dict


def recall_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    retrieved_k = set(retrieved_ids[:k])
    return len(retrieved_k & relevant_ids) / len(relevant_ids)


def precision_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    if k == 0:
        return 0.0
    retrieved_k = set(retrieved_ids[:k])
    return len(retrieved_k & relevant_ids) / k


def mrr(retrieved_ids: List[str], relevant_ids: Set[str]) -> float:
    for i, rid in enumerate(retrieved_ids, start=1):
        if rid in relevant_ids:
            return 1.0 / i
    return 0.0


def hit_rate(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    retrieved_k = set(retrieved_ids[:k])
    return 1.0 if retrieved_k & relevant_ids else 0.0


def ndcg_at_k(retrieved_ids: List[str], relevance_scores: Dict[str, float], k: int) -> float:
    """Normalized Discounted Cumulative Gain at k."""
    if k == 0:
        return 0.0
    dcg = 0.0
    for i, rid in enumerate(retrieved_ids[:k], start=1):
        rel = relevance_scores.get(rid, 0.0)
        dcg += rel / np.log2(i + 1)
    # Ideal DCG: sort by relevance descending
    ideal_rel = sorted(relevance_scores.values(), reverse=True)
    idcg = 0.0
    for i, rel in enumerate(ideal_rel[:k], start=1):
        idcg += rel / np.log2(i + 1)
    return dcg / idcg if idcg > 0 else 0.0