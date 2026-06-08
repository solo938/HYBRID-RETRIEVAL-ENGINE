"""
Evaluation runner for full hybrid retrieval (Dense + BM25 + RRF)
"""
import json
import numpy as np
from pathlib import Path
import sys

# Fix import path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import directly from the file path
import importlib.util
spec = importlib.util.spec_from_file_location(
    "hybrid_retriever_full",
    Path(__file__).parent.parent.parent / "retrieval" / "hybrid_retriever_full.py"
)
hybrid_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hybrid_module)
HybridRetrieverFull = hybrid_module.HybridRetrieverFull

def recall_at_k(retrieved, relevant, k):
    if not relevant:
        return 0.0
    return len(set(retrieved[:k]) & set(relevant)) / len(set(relevant))

def mrr_score(retrieved, relevant):
    relevant_set = set(relevant)
    for i, doc in enumerate(retrieved, 1):
        if doc in relevant_set:
            return 1.0 / i
    return 0.0

def ndcg_at_k(retrieved, relevant, k):
    relevant_set = set(relevant)
    dcg = sum(1.0 / np.log2(i + 2) for i, doc in enumerate(retrieved[:k]) if doc in relevant_set)
    idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(relevant_set), k)))
    return dcg / idcg if idcg > 0 else 0.0

def run_evaluation(split="dev", max_queries=75):
    print("\n" + "=" * 60)
    print("📊 HYBRID RETRIEVAL EVALUATION (Dense + BM25 + RRF)")
    print("=" * 60 + "\n")

    goldens = Path("app/evaluation/datasets/goldens")
    
    with open(goldens / f"eval_splits/retrieval_eval_{split}.json") as f:
        queries = json.load(f)
    print(f"📝 Loaded {len(queries)} queries from {split} split")
    
    with open(goldens / "relevant_docs.json") as f:
        rel_data = json.load(f)
    relevance_map = {item["query_id"]: item["chunk_ids"] for item in rel_data}
    
    retriever = HybridRetrieverFull()
    
    r5, r10, mrr_scores, ndcg_scores = [], [], [], []
    
    for i, q in enumerate(queries[:max_queries]):
        relevant = relevance_map.get(q["id"], [])
        results = retriever.search(q["text"], limit=10)
        retrieved = [r["chunk_id"] for r in results]
        
        r5.append(recall_at_k(retrieved, relevant, 5))
        r10.append(recall_at_k(retrieved, relevant, 10))
        mrr_scores.append(mrr_score(retrieved, relevant))
        ndcg_scores.append(ndcg_at_k(retrieved, relevant, 10))
        
        if (i + 1) % 25 == 0:
            print(f"  ✅ Processed {i+1}/{max_queries}")
    
    avg = lambda lst: sum(lst) / len(lst) if lst else 0.0
    metrics = {
        "recall@5": avg(r5),
        "recall@10": avg(r10),
        "mrr": avg(mrr_scores),
        "ndcg@10": avg(ndcg_scores),
    }
    
    print("\n" + "=" * 60)
    print("📊 HYBRID RETRIEVAL RESULTS")
    print("=" * 60)
    for k, v in metrics.items():
        bar = "█" * int(v * 40)
        pad = "░" * (40 - len(bar))
        print(f"{k:<12}: {v:.4f}  {bar}{pad}")
    
    # Show improvement over baseline
    baseline_file = goldens / "eval_results_baseline.json"
    if baseline_file.exists():
        with open(baseline_file) as f:
            baseline = json.load(f)
        
        print("\n📈 IMPROVEMENT OVER BASELINE")
        print("-" * 40)
        for metric in metrics:
            if metric in baseline:
                improvement = (metrics[metric] - baseline[metric]) / baseline[metric] * 100
                print(f"  {metric:<12}: {baseline[metric]:.3f} → {metrics[metric]:.3f} (+{improvement:.1f}%)")
    
    # Save
    out = goldens / "eval_results_hybrid_full.json"
    with open(out, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n💾 Saved to {out}")
    
    return metrics

if __name__ == "__main__":
    results = run_evaluation()
    
    print("\n" + "=" * 60)
    print("🎯 NEXT: Add cross-encoder reranking to boost further")
    print("=" * 60)
