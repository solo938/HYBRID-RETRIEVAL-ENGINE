"""
Evaluation runner with real hybrid retriever integration
"""
import json
import sys
from pathlib import Path
from typing import List, Dict

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.retrieval.retriever_connector import get_retriever

class RealRetrievalEvaluator:
    """Evaluate REAL hybrid retrieval performance"""
    
    def __init__(self, goldens_dir: str = "app/evaluation/datasets/goldens"):
        self.goldens_dir = Path(goldens_dir)
        self.retriever = get_retriever()
        self.results = {}
    
    def load_golden_queries(self, split: str = "dev") -> List[Dict]:
        """Load golden queries from split"""
        split_file = self.goldens_dir / f"eval_splits/retrieval_eval_{split}.json"
        with open(split_file, 'r') as f:
            return json.load(f)
    
    def load_relevance_judgments(self) -> Dict:
        """Load relevance judgments"""
        with open(self.goldens_dir / "relevant_docs.json", 'r') as f:
            judgments = json.load(f)
        return {j["query_id"]: j["chunk_ids"] for j in judgments}
    
    def calculate_recall_at_k(self, retrieved: List[str], relevant: List[str], k: int) -> float:
        if not relevant:
            return 0.0
        retrieved_k = set(retrieved[:k])
        relevant_set = set(relevant)
        hits = len(retrieved_k & relevant_set)
        return hits / len(relevant_set)
    
    def calculate_mrr(self, retrieved: List[str], relevant: List[str]) -> float:
        for i, doc in enumerate(retrieved, 1):
            if doc in relevant:
                return 1.0 / i
        return 0.0
    
    def calculate_ndcg(self, retrieved: List[str], relevant: List[str], k: int = 10) -> float:
        if not relevant:
            return 0.0
        
        relevance = {doc: 2 for doc in relevant}
        
        dcg = 0.0
        for i, doc in enumerate(retrieved[:k], 1):
            rel = relevance.get(doc, 0)
            dcg += rel / (i + 1)
        
        ideal_relevance = [2] * min(len(relevant), k)
        idcg = sum(rel / (i + 1) for i, rel in enumerate(ideal_relevance))
        
        return dcg / idcg if idcg > 0 else 0.0
    
    def run_evaluation(self, split: str = "dev", k_values: List[int] = [5, 10]):
        """Run complete evaluation with real retriever"""
        print(f"\n Running evaluation on {split} split...")
        print("=" * 50)
        
        queries = self.load_golden_queries(split)
        relevance_judgments = self.load_relevance_judgments()
        
        print(f" Loaded {len(queries)} queries")
        print(f"🔍 Testing retrieval...")
        
        metrics = {f"recall@{k}": [] for k in k_values}
        metrics["mrr"] = []
        metrics[f"ndcg@{k_values[-1]}"] = []
        
        for i, query_item in enumerate(queries):
            query_id = query_item["id"]
            query_text = query_item["text"]
            relevant = relevance_judgments.get(query_id, [])
            
            # REAL RETRIEVAL - uses your hybrid system
            retrieved = self.retriever.retrieve(query_text, top_k=max(k_values))
            
            # Calculate metrics
            for k in k_values:
                recall = self.calculate_recall_at_k(retrieved, relevant, k)
                metrics[f"recall@{k}"].append(recall)
            
            metrics["mrr"].append(self.calculate_mrr(retrieved, relevant))
            metrics[f"ndcg@{k_values[-1]}"].append(
                self.calculate_ndcg(retrieved, relevant, k_values[-1])
            )
            
            # Progress indicator
            if (i + 1) % 25 == 0:
                print(f"  Processed {i + 1}/{len(queries)} queries...")
        
        # Average results
        results = {}
        print("\n" + "=" * 50)
        print("📊 FINAL RESULTS:")
        print("=" * 50)
        
        for metric, values in metrics.items():
            avg_value = sum(values) / len(values) if values else 0
            results[metric] = avg_value
            print(f"{metric:15}: {avg_value:.4f}")
        
        return results
    
    def save_results(self, results: Dict, split: str = "dev"):
        """Save evaluation results"""
        output_file = self.goldens_dir / f"eval_results_real_{split}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "split": split,
                "metrics": results,
                "timestamp": "2025-06-08",
                "retriever": "hybrid"
            }, f, indent=2)
        print(f"\n Results saved to {output_file}")

if __name__ == "__main__":
    evaluator = RealRetrievalEvaluator()
    
    # Run on dev split
    results = evaluator.run_evaluation(split="dev", k_values=[5, 10])
    
    # Save results
    evaluator.save_results(results, split="dev")
    
    print("\n" + "=" * 50)
    print(" Next: Run on test split when ready")
    print("python app/evaluation/harness/evaluation_runner_v2.py --split test")
