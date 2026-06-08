"""
CI Quality Gate — runs on every push/PR
Fails the pipeline if metrics drop below thresholds
"""
import json
import sys
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

THRESHOLDS = {
    "recall@5":  0.35,
    "recall@10": 0.65,
    "mrr":       0.18,
    "ndcg@10":   0.28,
}

def recall_at_k(retrieved, relevant, k):
    if not relevant: return 0.0
    return len(set(retrieved[:k]) & set(relevant)) / len(set(relevant))

def mrr_score(retrieved, relevant):
    for i, doc in enumerate(retrieved, 1):
        if doc in set(relevant): return 1.0/i
    return 0.0

def ndcg_at_k(retrieved, relevant, k):
    rel = set(relevant)
    dcg  = sum(1/np.log2(i+2) for i,d in enumerate(retrieved[:k]) if d in rel)
    idcg = sum(1/np.log2(i+2) for i in range(min(len(rel),k)))
    return dcg/idcg if idcg else 0.0

def run_gate():
    print("🚦 RAG EVALUATION QUALITY GATE")
    print("="*50)

    goldens = Path("app/evaluation/datasets/goldens")

    with open(goldens / "questions.json") as f:
        questions = json.load(f)

    documents = [{"chunk_id": q["id"], "text": q.get("context","")}
                 for q in questions if q.get("context","")]
    relevance_map = {q["id"]: [q["id"]] for q in questions}

    with open(goldens / "eval_splits/retrieval_eval_dev.json") as f:
        eval_queries = json.load(f)

    print("Loading model...")
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    embeddings = model.encode([d["text"] for d in documents],
                               normalize_embeddings=True)

    r5, r10, mrr_scores, ndcg_scores = [], [], [], []

    for q in eval_queries[:30]:
        relevant = relevance_map.get(q["id"], [q["id"]])
        q_emb = model.encode(q["text"], normalize_embeddings=True)
        scores = embeddings @ q_emb
        top_idx = np.argsort(scores)[-10:][::-1]
        retrieved = [documents[j]["chunk_id"] for j in top_idx]

        r5.append(recall_at_k(retrieved, relevant, 5))
        r10.append(recall_at_k(retrieved, relevant, 10))
        mrr_scores.append(mrr_score(retrieved, relevant))
        ndcg_scores.append(ndcg_at_k(retrieved, relevant, 10))

    avg = lambda l: sum(l)/len(l) if l else 0
    metrics = {
        "recall@5":  avg(r5),
        "recall@10": avg(r10),
        "mrr":       avg(mrr_scores),
        "ndcg@10":   avg(ndcg_scores),
        "num_queries": 30,
        "commit": __import__("os").environ.get("GITHUB_SHA","local")[:8]
    }

    print("\n📊 RESULTS")
    print("-"*50)
    passed = True
    for metric, threshold in THRESHOLDS.items():
        value = metrics[metric]
        ok = value >= threshold
        status = "✅ PASS" if ok else "❌ FAIL"
        bar = "█" * int(value*30)
        print(f"{status}  {metric:<12} {value:.4f}  {bar}  (min: {threshold})")
        if not ok:
            passed = False

    with open(goldens / "eval_results_ci.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("\n" + "="*50)
    if passed:
        print("✅ ALL QUALITY GATES PASSED — safe to merge")
        sys.exit(0)
    else:
        print("❌ QUALITY GATE FAILED — merge blocked")
        sys.exit(1)

if __name__ == "__main__":
    run_gate()
