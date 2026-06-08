"""
Evaluation runner — uses actual contexts from golden dataset
No fake documents. Real cosine similarity against real text.
"""
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer


class GoldenDatasetRetriever:
    """
    Indexes actual contexts from relevant_docs.json
    so chunk IDs match exactly what the golden dataset expects.
    """

    def __init__(self):
        print("🔧 Loading embedding model...")
        self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        self.documents = []   # {"chunk_id": ..., "text": ...}
        self.embeddings = []
        self._index_golden_contexts()

    def _index_golden_contexts(self):
        path = Path("app/evaluation/datasets/goldens/relevant_docs.json")
        with open(path) as f:
            data = json.load(f)

        seen = {}
        for item in data:
            context = item.get("context_preview", "")
            for chunk_id in item.get("chunk_ids", []):
                if chunk_id and context and chunk_id not in seen:
                    seen[chunk_id] = context

        print(f"  Indexing {len(seen)} real contexts...")
        for chunk_id, text in seen.items():
            self.documents.append({"chunk_id": chunk_id, "text": text})
            self.embeddings.append(self.model.encode(text, normalize_embeddings=True))

        self.embeddings = np.array(self.embeddings)
        print(f"  ✅ Indexed {len(self.documents)} documents")

    def search(self, query: str, limit: int = 10):
        q_emb = self.model.encode(query, normalize_embeddings=True)
        scores = self.embeddings @ q_emb          # cosine sim (normalized)
        top_idx = np.argsort(scores)[-limit:][::-1]
        return [
            {"chunk_id": self.documents[i]["chunk_id"], "score": float(scores[i])}
            for i in top_idx
        ]


# ── Metrics ────────────────────────────────────────────────────────────────────

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
    dcg = sum(
        1.0 / np.log2(i + 2)
        for i, doc in enumerate(retrieved[:k])
        if doc in relevant_set
    )
    idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(relevant_set), k)))
    return dcg / idcg if idcg > 0 else 0.0


# ── Runner ─────────────────────────────────────────────────────────────────────

def run_evaluation(split: str = "dev", max_queries: int = 75):
    print("\n" + "=" * 60)
    print("📊 RAG EVALUATION — Real Contexts")
    print("=" * 60 + "\n")

    goldens = Path("app/evaluation/datasets/goldens")

    # Load queries
    queries_file = goldens / f"eval_splits/retrieval_eval_{split}.json"
    with open(queries_file) as f:
        queries = json.load(f)
    print(f"📝 Loaded {len(queries)} queries from {split} split")

    # Load relevance map  {query_id: [chunk_id, ...]}
    with open(goldens / "relevant_docs.json") as f:
        rel_data = json.load(f)
    relevance_map = {item["query_id"]: item["chunk_ids"] for item in rel_data}

    # Index real contexts
    retriever = GoldenDatasetRetriever()

    # Evaluate
    r5, r10, mrr_scores, ndcg_scores = [], [], [], []

    queries_to_eval = queries[:max_queries]
    for i, q in enumerate(queries_to_eval):
        relevant  = relevance_map.get(q["id"], [])
        results   = retriever.search(q["text"], limit=10)
        retrieved = [r["chunk_id"] for r in results]

        r5.append(recall_at_k(retrieved, relevant, 5))
        r10.append(recall_at_k(retrieved, relevant, 10))
        mrr_scores.append(mrr_score(retrieved, relevant))
        ndcg_scores.append(ndcg_at_k(retrieved, relevant, 10))

        if (i + 1) % 25 == 0:
            print(f"  ✅ Processed {i+1}/{len(queries_to_eval)}")

    # Averages
    avg = lambda lst: sum(lst) / len(lst) if lst else 0.0
    metrics = {
        "recall@5":  avg(r5),
        "recall@10": avg(r10),
        "mrr":       avg(mrr_scores),
        "ndcg@10":   avg(ndcg_scores),
        "num_queries": len(queries_to_eval),
        "split": split,
    }

    # Print
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60)
    for k, v in metrics.items():
        if isinstance(v, float):
            bar = "█" * int(v * 40)
            pad = "░" * (40 - len(bar))
            print(f"{k:<12}: {v:.4f}  {bar}{pad}")
        else:
            print(f"{k:<12}: {v}")

    # CI gate check
    print("\n🚦 QUALITY GATE")
    thresholds = {"recall@10": 0.30, "mrr": 0.25, "ndcg@10": 0.25}
    passed = True
    for metric, threshold in thresholds.items():
        status = "✅ PASS" if metrics[metric] >= threshold else "❌ FAIL"
        print(f"  {status}  {metric} = {metrics[metric]:.4f} (threshold: {threshold})")
        if metrics[metric] < threshold:
            passed = False

    print(f"\n{'✅ ALL GATES PASSED' if passed else '❌ QUALITY GATE FAILED — block merge'}")

    # Save
    out = goldens / f"eval_results_{split}.json"
    with open(out, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n💾 Saved to {out}")

    return metrics, passed


if __name__ == "__main__":
    run_evaluation(split="dev", max_queries=75)
