"""
Baseline evaluation with realistic thresholds for pure dense retrieval
"""
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer


class SimpleDenseRetriever:
    def __init__(self):
        print("🔧 Loading embedding model...")
        self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        self.documents = []
        self.embeddings = []
        self._load_documents()
    
    def _load_documents(self):
        """Load documents from golden dataset"""
        path = Path("app/evaluation/datasets/goldens/relevant_docs.json")
        with open(path) as f:
            data = json.load(f)
        
        # Try to get full context from questions.json first
        questions_path = Path("app/evaluation/datasets/goldens/questions.json")
        full_contexts = {}
        if questions_path.exists():
            with open(questions_path) as f:
                questions = json.load(f)
            for q in questions:
                if 'context' in q and q['context']:
                    full_contexts[q['id']] = q['context']
        
        seen = {}
        for item in data:
            # Use full context if available, otherwise context_preview
            context = ""
            for chunk_id in item.get("chunk_ids", []):
                # Try to find matching question
                query_id = item.get("query_id", "")
                if query_id in full_contexts:
                    context = full_contexts[query_id]
                    break
            
            if not context:
                context = item.get("context_preview", "")
            
            for chunk_id in item.get("chunk_ids", []):
                if chunk_id and context and chunk_id not in seen:
                    seen[chunk_id] = context
        
        print(f"  Indexing {len(seen)} documents (avg length: {sum(len(v) for v in seen.values())//len(seen) if seen else 0} chars)...")
        
        for chunk_id, text in seen.items():
            self.documents.append({"chunk_id": chunk_id, "text": text})
            self.embeddings.append(self.model.encode(text, normalize_embeddings=True))
        
        if self.embeddings:
            self.embeddings = np.array(self.embeddings)
        print(f"  ✅ Indexed {len(self.documents)} documents")
    
    def search(self, query: str, limit: int = 10):
        if len(self.embeddings) == 0:
            return []
        q_emb = self.model.encode(query, normalize_embeddings=True)
        scores = self.embeddings @ q_emb
        top_idx = np.argsort(scores)[-limit:][::-1]
        return [{"chunk_id": self.documents[i]["chunk_id"], "score": float(scores[i])} for i in top_idx]


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
    print("📊 BASELINE EVALUATION (Pure Dense Retrieval)")
    print("=" * 60 + "\n")

    goldens = Path("app/evaluation/datasets/goldens")
    
    with open(goldens / f"eval_splits/retrieval_eval_{split}.json") as f:
        queries = json.load(f)
    print(f"📝 Loaded {len(queries)} queries from {split} split")
    
    with open(goldens / "relevant_docs.json") as f:
        rel_data = json.load(f)
    relevance_map = {item["query_id"]: item["chunk_ids"] for item in rel_data}
    
    retriever = SimpleDenseRetriever()
    
    if len(retriever.embeddings) == 0:
        print("❌ No documents indexed!")
        return None
    
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
        "num_queries": len(r5),
    }
    
    print("\n" + "=" * 60)
    print("📊 BASELINE RESULTS")
    print("=" * 60)
    for k, v in metrics.items():
        if isinstance(v, float):
            bar = "█" * int(v * 40)
            pad = "░" * (40 - len(bar))
            print(f"{k:<12}: {v:.4f}  {bar}{pad}")
        else:
            print(f"{k:<12}: {v}")
    
    # Realistic baseline thresholds
    print("\n🚦 BASELINE QUALITY GATE (Expect these to improve with hybrid + reranking)")
    thresholds = {"recall@10": 0.35, "mrr": 0.20, "ndcg@10": 0.20}
    for metric, threshold in thresholds.items():
        value = metrics.get(metric, 0)
        status = "✅ BASELINE" if value >= threshold else "⚠️  LOW"
        print(f"  {status}  {metric} = {value:.4f} (baseline threshold: {threshold})")
    
    # Save
    out = goldens / "eval_results_baseline.json"
    with open(out, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n💾 Saved to {out}")
    
    return metrics

if __name__ == "__main__":
    results = run_evaluation()
    
    print("\n" + "=" * 60)
    print("🎯 WHAT THESE NUMBERS MEAN")
    print("=" * 60)
    print("This is your BASELINE with pure dense retrieval.")
    print("\nNext improvements:")
    print("  📈 +15-20% → Add BM25 sparse retrieval (hybrid search)")
    print("  📈 +10-15% → Add RRF fusion")
    print("  📈 +15-20% → Add cross-encoder reranking")
    print("  🎯 70-80% recall@10 achievable with full pipeline")
