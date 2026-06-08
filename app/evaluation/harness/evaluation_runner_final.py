"""
Final evaluation runner with real retriever and golden dataset
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "app"))

from app.retrieval.real_retriever import RealRetriever

class FinalEvaluationRunner:
    def __init__(self):
        self.goldens_dir = Path("app/evaluation/datasets/goldens")
        print("🚀 Initializing Final Evaluation Runner...")
        self.retriever = RealRetriever()
    
    def load_queries(self, split: str = "dev") -> list:
        split_file = self.goldens_dir / f"eval_splits/retrieval_eval_{split}.json"
        with open(split_file, 'r') as f:
            return json.load(f)
    
    def load_relevance(self) -> dict:
        with open(self.goldens_dir / "relevant_docs.json", 'r') as f:
            judgments = json.load(f)
        return {j["query_id"]: j["chunk_ids"] for j in judgments}
    
    def recall_at_k(self, retrieved: list, relevant: list, k: int) -> float:
        if not relevant:
            return 0.0
        retrieved_set = set(retrieved[:k])
        relevant_set = set(relevant)
        return len(retrieved_set & relevant_set) / len(relevant_set)
    
    def mrr(self, retrieved: list, relevant: list) -> float:
        for i, doc in enumerate(retrieved, 1):
            if doc in relevant:
                return 1.0 / i
        return 0.0
    
    def run(self, split: str = "dev", max_queries: int = None):
        print(f"\n{'='*60}")
        print(f"📊 FINAL EVALUATION on {split.upper()} Split")
        print(f"{'='*60}\n")
        
        queries = self.load_queries(split)
        relevance = self.load_relevance()
        
        if max_queries:
            queries = queries[:max_queries]
        
        print(f"📝 Loaded {len(queries)} queries")
        
        recall_5_scores = []
        recall_10_scores = []
        mrr_scores = []
        
        for i, q in enumerate(queries):
            query_text = q["text"]
            query_id = q["id"]
            relevant = relevance.get(query_id, [])
            
            # Search with real retriever
            results = self.retriever.search(query_text, limit=10)
            retrieved = [r["chunk_id"] for r in results]
            
            # Calculate metrics
            recall_5_scores.append(self.recall_at_k(retrieved, relevant, 5))
            recall_10_scores.append(self.recall_at_k(retrieved, relevant, 10))
            mrr_scores.append(self.mrr(retrieved, relevant))
            
            if (i + 1) % 20 == 0:
                print(f"  ✅ Processed {i + 1}/{len(queries)} queries")
        
        # Calculate averages
        avg_recall_5 = sum(recall_5_scores) / len(recall_5_scores) if recall_5_scores else 0
        avg_recall_10 = sum(recall_10_scores) / len(recall_10_scores) if recall_10_scores else 0
        avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0
        
        print(f"\n{'='*60}")
        print("📊 FINAL RESULTS")
        print(f"{'='*60}")
        print(f"Recall@5 : {avg_recall_5:.4f}")
        print(f"Recall@10: {avg_recall_10:.4f}")
        print(f"MRR      : {avg_mrr:.4f}")
        
        # Visual bars
        print(f"\n📈 Performance Visualization:")
        bar5 = "█" * int(avg_recall_5 * 50)
        bar10 = "█" * int(avg_recall_10 * 50)
        bar_mrr = "█" * int(avg_mrr * 50)
        print(f"Recall@5 : {bar5}{'░' * (50 - len(bar5))} {avg_recall_5:.1%}")
        print(f"Recall@10: {bar10}{'░' * (50 - len(bar10))} {avg_recall_10:.1%}")
        print(f"MRR      : {bar_mrr}{'░' * (50 - len(bar_mrr))} {avg_mrr:.1%}")
        
        # Save results
        results = {
            "split": split,
            "recall@5": avg_recall_5,
            "recall@10": avg_recall_10,
            "mrr": avg_mrr,
            "num_queries": len(queries)
        }
        
        output_file = self.goldens_dir / f"final_results_{split}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Results saved to {output_file}")
        
        # Recommendations
        print(f"\n{'='*60}")
        print("🎯 RECOMMENDATIONS")
        print(f"{'='*60}")
        if avg_recall_5 < 0.5:
            print("⚠️  Scores are low. To improve:")
            print("   1. Index MORE documents (currently limited to 100)")
            print("   2. Use real documents instead of mock text")
            print("   3. Add hybrid search (BM25 + dense)")
            print("   4. Implement cross-encoder reranking")
        else:
            print("✅ Great! Your retriever is working well!")
            print("   Next: Add reranking to boost to 0.85+")
        
        return results

if __name__ == "__main__":
    runner = FinalEvaluationRunner()
    
    # Run on dev split (limit to 50 queries for speed)
    results = runner.run(split="dev", max_queries=50)
    
    print("\n🎯 Next: Run on test split")
    print("   python -c 'from app.evaluation.harness.evaluation_runner_final import FinalEvaluationRunner; runner = FinalEvaluationRunner(); runner.run(split=\"test\", max_queries=50)'")
