"""
Evaluation runner directly connected to your hybrid retriever
"""
import json
import sys
import os
from pathlib import Path
from typing import List, Dict

# Add project root to path properly
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "app"))

# Now import your existing retrievers
try:
    from app.retrieval.hybrid_retriever import HybridRetriever
    from app.retrieval.dense_retriever import DenseRetriever
    from app.retrieval.sparse_retriever import SparseRetriever
    HAS_RETRIEVERS = True
    print("✅ Connected to existing retrievers")
except ImportError as e:
    print(f"⚠️ Could not import retrievers: {e}")
    print("Creating minimal retrievers...")
    HAS_RETRIEVERS = False

class EvaluationRunner:
    def __init__(self):
        self.goldens_dir = Path("app/evaluation/datasets/goldens")
        
        # Initialize retrievers
        if HAS_RETRIEVERS:
            try:
                self.hybrid_retriever = HybridRetriever()
                print("  ✅ HybridRetriever initialized")
            except Exception as e:
                print(f"  ⚠️ HybridRetriever failed: {e}")
                self.hybrid_retriever = None
        else:
            self.hybrid_retriever = None
            self._create_minimal_retrievers()
    
    def _create_minimal_retrievers(self):
        """Create minimal retrievers for testing"""
        print("  Creating minimal retrievers...")
        
        class MinimalHybridRetriever:
            def __init__(self):
                print("    MinimalHybridRetriever created")
            
            def search(self, query, limit=10):
                # Return mock results based on query
                import hashlib
                results = []
                for i in range(limit):
                    query_hash = hashlib.md5(query.encode()).hexdigest()[:16]
                    chunk_id = f"chunk_{query_hash}_{i}"
                    results.append({
                        "chunk_id": chunk_id,
                        "score": 1.0 / (i + 1),
                        "text": f"Mock result for: {query}"
                    })
                return results
        
        self.hybrid_retriever = MinimalHybridRetriever()
    
    def load_queries(self, split: str = "dev") -> List[Dict]:
        """Load queries from golden dataset"""
        split_file = self.goldens_dir / f"eval_splits/retrieval_eval_{split}.json"
        if not split_file.exists():
            print(f"❌ Split file not found: {split_file}")
            return []
        
        with open(split_file, 'r') as f:
            return json.load(f)
    
    def load_relevance(self) -> Dict:
        """Load relevance judgments"""
        relevance_file = self.goldens_dir / "relevant_docs.json"
        if not relevance_file.exists():
            print(f"❌ Relevance file not found: {relevance_file}")
            return {}
        
        with open(relevance_file, 'r') as f:
            judgments = json.load(f)
        
        # Convert to dict keyed by query_id
        return {j["query_id"]: j["chunk_ids"] for j in judgments}
    
    def recall_at_k(self, retrieved: List[str], relevant: List[str], k: int) -> float:
        if not relevant:
            return 0.0
        retrieved_set = set(retrieved[:k])
        relevant_set = set(relevant)
        return len(retrieved_set & relevant_set) / len(relevant_set)
    
    def mrr(self, retrieved: List[str], relevant: List[str]) -> float:
        for i, doc in enumerate(retrieved, 1):
            if doc in relevant:
                return 1.0 / i
        return 0.0
    
    def ndcg_at_k(self, retrieved: List[str], relevant: List[str], k: int = 10) -> float:
        if not relevant:
            return 0.0
        
        relevance = {doc: 2 for doc in relevant}
        
        dcg = 0.0
        for i, doc in enumerate(retrieved[:k], 1):
            rel = relevance.get(doc, 0)
            dcg += rel / (i + 1)
        
        ideal = [2] * min(len(relevant), k)
        idcg = sum(rel / (i + 1) for i, rel in enumerate(ideal))
        
        return dcg / idcg if idcg > 0 else 0.0
    
    def run(self, split: str = "dev", k_values: List[int] = [5, 10]):
        """Run evaluation on specific split"""
        print(f"\n{'='*60}")
        print(f"📊 Running Evaluation on {split.upper()} Split")
        print(f"{'='*60}\n")
        
        # Load data
        queries = self.load_queries(split)
        relevance = self.load_relevance()
        
        if not queries:
            print("❌ No queries loaded")
            return None
        
        print(f"📝 Loaded {len(queries)} queries")
        print(f"🔍 Testing retrieval...\n")
        
        # Initialize metrics
        metrics = {f"recall@{k}": [] for k in k_values}
        metrics["mrr"] = []
        metrics[f"ndcg@{k_values[-1]}"] = []
        
        # Run evaluation
        for i, query_item in enumerate(queries):
            query_id = query_item["id"]
            query_text = query_item["text"]
            relevant = relevance.get(query_id, [])
            
            # Get retrieval results from your hybrid retriever
            retrieved = []
            try:
                results = self.hybrid_retriever.search(query_text, limit=max(k_values))
                # Extract chunk_id safely
                for r in results:
                    if isinstance(r, dict):
                        chunk_id = r.get("chunk_id") or r.get("id") or r.get("doc_id")
                        if chunk_id:
                            retrieved.append(chunk_id)
                        else:
                            retrieved.append(f"result_{len(retrieved)}")
                    else:
                        retrieved.append(str(r))
            except Exception as e:
                print(f"  ⚠️ Query {query_id} failed: {e}")
                retrieved = []
            
            # Calculate metrics
            for k in k_values:
                metrics[f"recall@{k}"].append(self.recall_at_k(retrieved, relevant, k))
            
            metrics["mrr"].append(self.mrr(retrieved, relevant))
            metrics[f"ndcg@{k_values[-1]}"].append(
                self.ndcg_at_k(retrieved, relevant, k_values[-1])
            )
            
            # Progress
            if (i + 1) % 50 == 0:
                print(f"  ✅ Processed {i + 1}/{len(queries)} queries")
        
        # Average results
        print(f"\n{'='*60}")
        print("📊 RESULTS")
        print(f"{'='*60}")
        
        results = {}
        for metric, values in metrics.items():
            avg = sum(values) / len(values) if values else 0
            results[metric] = avg
            # Visual indicator
            bar_length = int(avg * 50)
            bar = "█" * bar_length + "░" * (50 - bar_length)
            print(f"{metric:12}: {avg:.4f}  {bar}")
        
        # Save results
        output_file = self.goldens_dir / f"eval_results_{split}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "split": split,
                "metrics": results,
                "num_queries": len(queries),
                "retriever": "hybrid"
            }, f, indent=2)
        
        print(f"\n✅ Results saved to {output_file}")
        
        return results

if __name__ == "__main__":
    runner = EvaluationRunner()
    
    # Run on dev split
    runner.run(split="dev", k_values=[5, 10])
    
    print(f"\n{'='*60}")
    print("🎯 Next Steps:")
    print("  1. Run on test split: python -c 'from app.evaluation.harness.evaluation_runner import EvaluationRunner; runner = EvaluationRunner(); runner.run(split=\"test\")'")
    print("  2. Once you have real scores, add reranking")
    print("  3. Set up CI/CD gates with thresholds")
    print(f"{'='*60}")
