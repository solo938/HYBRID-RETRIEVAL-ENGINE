"""Regression testing for retrieval quality."""
from pathlib import Path
from app.retrieval.hybrid_retriever import HybridRetriever
from app.evaluation.evaluators.retrieval_evaluator import RetrievalEvaluator


class RegressionRunner:
    def __init__(self, retriever: HybridRetriever, gold_path: Path, thresholds: dict = None):
        self.evaluator = RetrievalEvaluator(retriever, gold_path)
        self.thresholds = thresholds or {
            "recall@10": 0.70,
            "mrr": 0.65,
            "ndcg@10": 0.70,
        }

    def run(self) -> bool:
        metrics = self.evaluator.evaluate(top_k=10)
        passed = True
        for key, threshold in self.thresholds.items():
            value = metrics.get(key, 0)
            if value < threshold:
                print(f"❌ Regression: {key} = {value} < {threshold}")
                passed = False
            else:
                print(f"✅ {key} = {value} >= {threshold}")
        return passed