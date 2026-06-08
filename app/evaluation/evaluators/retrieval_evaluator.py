"""Run retrieval evaluation on a gold dataset."""
from typing import List, Dict, Any
from pathlib import Path
from app.retrieval.hybrid_retriever import HybridRetriever
from app.evaluation.metrics.retrieval_metrics import recall_at_k, mrr, ndcg_at_k, precision_at_k, hit_rate
from app.evaluation.datasets.dataset_loader import RetrievalDatasetLoader, RetrievalSample


class RetrievalEvaluator:
    def __init__(self, retriever: HybridRetriever, gold_path: Path):
        self.retriever = retriever
        if gold_path.suffix == ".jsonl":
            self.samples = RetrievalDatasetLoader.load_jsonl(gold_path)
        else:
            self.samples = RetrievalDatasetLoader.load_json(gold_path)

    def evaluate(self, top_k: int = 10) -> Dict[str, float]:
        recalls, mrrs, hit_rates, precisions, ndcgs = [], [], [], [], []
        for sample in self.samples:
            result = self.retriever.retrieve(sample.query, top_k=top_k)
            retrieved_ids = [c.chunk_id for c in result.results]
            recalls.append(recall_at_k(retrieved_ids, sample.relevant_chunk_ids, top_k))
            mrrs.append(mrr(retrieved_ids, sample.relevant_chunk_ids))
            hit_rates.append(hit_rate(retrieved_ids, sample.relevant_chunk_ids, top_k))
            precisions.append(precision_at_k(retrieved_ids, sample.relevant_chunk_ids, top_k))
            # nDCG with binary relevance
            relevance = {cid: 1.0 for cid in sample.relevant_chunk_ids}
            ndcgs.append(ndcg_at_k(retrieved_ids, relevance, top_k))

        return {
            f"recall@{top_k}": round(sum(recalls) / len(recalls), 4),
            f"precision@{top_k}": round(sum(precisions) / len(precisions), 4),
            f"hit_rate@{top_k}": round(sum(hit_rates) / len(hit_rates), 4),
            "mrr": round(sum(mrrs) / len(mrrs), 4),
            f"ndcg@{top_k}": round(sum(ndcgs) / len(ndcgs), 4),
        }