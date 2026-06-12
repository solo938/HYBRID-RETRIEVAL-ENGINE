#!/usr/bin/env python
"""
Evaluation with MiniLM reranker (120MB)
"""
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer, CrossEncoder

class RerankerEval:
    def __init__(self):
        print("🔧 Loading models...")
        print("  - Dense: BGE-small (already cached)")
        self.dense = SentenceTransformer("BAAI/bge-small-en-v1.5")
        print("  - Reranker: ms-marco-MiniLM-L-6-v2 (120MB - downloading...)")
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)
        self.docs = []
        self.embeddings = []
        self._load()
    
    def _load(self):
        path = Path("app/evaluation/datasets/goldens/relevant_docs.json")
        with open(path) as f:
            data = json.load(f)
        
        seen = {}
        for item in data:
            ctx = item.get("context_preview", "")
            for cid in item.get("chunk_ids", []):
                if cid and ctx and cid not in seen:
                    seen[cid] = ctx
        
        print(f"  Indexing {len(seen)} documents...")
        self.docs = [{"id": cid, "text": t} for cid, t in seen.items()]
        texts = [d["text"] for d in self.docs]
        print("  Generating dense embeddings...")
        self.embeddings = self.dense.encode(texts, normalize_embeddings=True)
        print(f"  ✅ Ready with {len(self.docs)} documents")
    
    def search(self, query, limit=10):
        q_emb = self.dense.encode(query, normalize_embeddings=True)
        scores = self.embeddings @ q_emb
        top_idx = np.argsort(scores)[-30:][::-1]
        
        candidates = [self.docs[i] for i in top_idx]
        pairs = [[query, c["text"]] for c in candidates]
        rerank_scores = self.reranker.predict(pairs)
        
        results = sorted(zip(candidates, rerank_scores), key=lambda x: x[1], reverse=True)
        return [{"chunk_id": r[0]["id"], "score": float(r[1])} for r in results[:limit]]

def recall_at_k(retrieved, relevant, k):
    if not relevant:
        return 0.0
    return len(set(retrieved[:k]) & set(relevant)) / len(set(relevant))

def mrr_score(retrieved, relevant):
    for i, doc in enumerate(retrieved, 1):
        if doc in relevant:
            return 1.0 / i
    return 0.0

def main():
    print("\n" + "="*60)
    print("📊 RERANKER EVALUATION (MiniLM - 120MB)")
    print("="*60 + "\n")
    
    goldens = Path("app/evaluation/datasets/goldens")
    
    with open(goldens / "eval_splits/retrieval_eval_dev.json") as f:
        queries = json.load(f)
    print(f"📝 Loaded {len(queries)} queries")
    
    with open(goldens / "relevant_docs.json") as f:
        rel_data = json.load(f)
    rel_map = {item["query_id"]: item["chunk_ids"] for item in rel_data}
    
    retriever = RerankerEval()
    
    r5_scores = []
    r10_scores = []
    mrr_scores = []
    
    for i, q in enumerate(queries[:50]):
        relevant = rel_map.get(q["id"], [])
        results = retriever.search(q["text"], limit=10)
        retrieved = [r["chunk_id"] for r in results]
        
        r5_scores.append(recall_at_k(retrieved, relevant, 5))
        r10_scores.append(recall_at_k(retrieved, relevant, 10))
        mrr_scores.append(mrr_score(retrieved, relevant))
        
        if (i+1) % 10 == 0:
            print(f"  ✅ Processed {i+1}/50")
    
    print("\n" + "="*60)
    print("📊 RESULTS WITH RERANKER")
    print("="*60)
    print(f"recall@5:  {np.mean(r5_scores):.1%}  ({np.mean(r5_scores):.3f})")
    print(f"recall@10: {np.mean(r10_scores):.1%}  ({np.mean(r10_scores):.3f})")
    print(f"MRR:       {np.mean(mrr_scores):.1%}  ({np.mean(mrr_scores):.3f})")
    
    # Compare with baseline
    baseline_file = goldens / "eval_results_baseline.json"
    if baseline_file.exists():
        with open(baseline_file) as f:
            baseline = json.load(f)
        
        print("\n📈 IMPROVEMENT VS BASELINE (Dense Only)")
        print("-" * 40)
        print(f"recall@10: {baseline['recall@10']:.1%} → {np.mean(r10_scores):.1%} (+{(np.mean(r10_scores)-baseline['recall@10'])*100:.1f}%)")
        print(f"MRR:       {baseline['mrr']:.1%} → {np.mean(mrr_scores):.1%} (+{(np.mean(mrr_scores)-baseline['mrr'])*100:.1f}%)")
    
    # Save results
    results = {
        "recall@5": float(np.mean(r5_scores)),
        "recall@10": float(np.mean(r10_scores)),
        "mrr": float(np.mean(mrr_scores)),
        "num_queries": 50
    }
    
    with open(goldens / "eval_results_reranker_minilm.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to {goldens / 'eval_results_reranker_minilm.json'}")

if __name__ == "__main__":
    main()
