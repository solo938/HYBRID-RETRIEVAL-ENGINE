"""
Evaluation runner with dense retrieval + cross-encoder reranking
"""
import json
import numpy as np
from pathlib import Path
import sys

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import reranker
from app.retrieval.reranker_cross_encoder import DenseRetrieverWithReranker

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
    print("📊 DENSE + CROSS-ENCODER RERANKER EVALUATION")
    print("=" * 60 + "\n")

    goldens = Path("app/evaluation/datasets/goldens")
    
    with open(goldens / f"eval_splits/retrieval_eval_{split}.json") as f:
        queries = json.load(f)
    print(f"📝 Loaded {len(queries)} queries from {split} split")
    
    with open(goldens / "relevant_docs.json") as f:
        rel_data = json.load(f)
    relevance_map = {item["query_id"]: item["chunk_ids"] for item in rel_data}
    
    print("\n⏳ Loading reranker (first time downloads ~1.4GB model)...")
    retriever = DenseRetrieverWithReranker()
    
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
    print("📊 DENSE + RERANKER RESULTS")
    print("=" * 60)
    for k, v in metrics.items():
        bar = "█" * int(v * 40)
        pad = "░" * (40 - len(bar))
        print(f"{k:<12}: {v:.4f}  {bar}{pad}")
    
    # Compare with baseline
    baseline_file = goldens / "eval_results_baseline.json"
    if baseline_file.exists():
        with open(baseline_file) as f:
            baseline = json.load(f)
        
        print("\n📈 IMPROVEMENT OVER BASELINE (Dense Only)")
        print("-" * 45)
        for metric in metrics:
            if metric in baseline and baseline[metric] > 0:
                improvement = (metrics[metric] - baseline[metric]) / baseline[metric] * 100
                arrow = "🟢" if improvement > 0 else "🔴"
                print(f"  {metric:<12}: {baseline[metric]:.3f} → {metrics[metric]:.3f} ({arrow} {improvement:+.1f}%)")
    
    # Save
    out = goldens / "eval_results_reranked.json"
    with open(out, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n💾 Saved to {out}")
    
    return metrics

if __name__ == "__main__":
    results = run_evaluation(max_queries=50)  # Run on 50 queries for speed
    
    print("\n" + "=" * 60)
    print("🎯 RESULTS WITH CROSS-ENCODER RERANKING")
    print("=" * 60)
    print(f"  recall@5:  {results['recall@5']:.1%}")
    print(f"  recall@10: {results['recall@10']:.1%}")
    print(f"  MRR:       {results['mrr']:.1%}")
    print(f"  nDCG@10:   {results['ndcg@10']:.1%}")
