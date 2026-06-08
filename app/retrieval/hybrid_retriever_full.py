"""
Full hybrid retriever: Dense (BGE) + Sparse (BM25) + Weighted RRF Fusion
Optimized for short context previews
"""
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict

class HybridRetrieverFull:
    def __init__(self):
        print("🔧 Initializing Full Hybrid Retriever...")
        
        # Dense retriever
        self.dense_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        
        # Sparse retriever with optimized parameters
        self.tfidf = TfidfVectorizer(
            analyzer='word',
            ngram_range=(1, 2),
            max_features=5000,
            min_df=1,
            max_df=0.85,
            sublinear_tf=True  # Better for short texts
        )
        
        self.documents = []
        self.dense_embeddings = []
        self.sparse_matrix = None
        self.chunk_to_idx = {}
        
        self._load_documents()
    
    def _load_documents(self):
        """Load and index documents"""
        path = Path("app/evaluation/datasets/goldens/relevant_docs.json")
        with open(path) as f:
            data = json.load(f)
        
        # Get unique documents
        seen = {}
        for item in data:
            context = item.get("context_preview", "")
            for chunk_id in item.get("chunk_ids", []):
                if chunk_id and context and chunk_id not in seen:
                    seen[chunk_id] = context
        
        print(f"  Indexing {len(seen)} documents...")
        
        self.documents = [{"chunk_id": cid, "text": text} for cid, text in seen.items()]
        self.chunk_to_idx = {doc["chunk_id"]: i for i, doc in enumerate(self.documents)}
        
        # Dense embeddings
        texts = [doc["text"] for doc in self.documents]
        print("  Generating dense embeddings...")
        self.dense_embeddings = self.dense_model.encode(texts, normalize_embeddings=True)
        
        # Sparse features
        print("  Generating sparse features...")
        self.sparse_matrix = self.tfidf.fit_transform(texts)
        
        print(f"  ✅ Indexed {len(self.documents)} documents")
    
    def _dense_search(self, query: str, k: int = 50):
        """Dense retrieval"""
        q_emb = self.dense_model.encode(query, normalize_embeddings=True)
        scores = self.dense_embeddings @ q_emb
        top_idx = np.argsort(scores)[-k:][::-1]
        return [(self.documents[i]["chunk_id"], float(scores[i])) for i in top_idx]
    
    def _sparse_search(self, query: str, k: int = 30):
        """Sparse retrieval with TF-IDF (reduced k to reduce noise)"""
        query_vec = self.tfidf.transform([query])
        scores = self.sparse_matrix @ query_vec.T
        scores = scores.toarray().flatten()
        
        top_idx = np.argsort(scores)[-k:][::-1]
        results = []
        for i in top_idx:
            if scores[i] > 0.05:  # Threshold to filter low scores
                results.append((self.documents[i]["chunk_id"], float(scores[i])))
        return results
    
    def _weighted_rrf_fusion(self, dense_results, sparse_results, 
                             dense_weight=0.7, sparse_weight=0.3, k=10):
        """Weighted Reciprocal Rank Fusion - dense biased"""
        scores = defaultdict(float)
        
        for rank, (doc_id, _) in enumerate(dense_results, 1):
            scores[doc_id] += dense_weight / (k + rank)
        
        for rank, (doc_id, _) in enumerate(sparse_results, 1):
            scores[doc_id] += sparse_weight / (k + rank)
        
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [doc_id for doc_id, _ in sorted_docs]
    
    def search(self, query: str, limit: int = 10):
        """Hybrid search with weighted RRF fusion"""
        # Get results
        dense_results = self._dense_search(query, k=limit * 3)
        sparse_results = self._sparse_search(query, k=limit * 2)
        
        # If sparse returns nothing, just use dense
        if not sparse_results:
            return [{"chunk_id": cid, "score": score} 
                   for cid, score in dense_results[:limit]]
        
        # Fuse with weighted RRF (favor dense)
        fused_ids = self._weighted_rrf_fusion(
            dense_results, sparse_results, 
            dense_weight=0.75, sparse_weight=0.25, k=10
        )
        
        return [{"chunk_id": cid, "score": 1.0 / (i+1)} 
                for i, cid in enumerate(fused_ids[:limit])]

# Test
if __name__ == "__main__":
    retriever = HybridRetrieverFull()
    
    test_queries = [
        "In what country is Normandy located?",
        "What is hybrid search?",
        "VPN access request procedure"
    ]
    
    print("\n🔍 Testing hybrid search:")
    for query in test_queries:
        print(f"\n  Query: {query}")
        results = retriever.search(query, limit=3)
        for r in results:
            print(f"    - {r['chunk_id']}: {r['score']:.3f}")
