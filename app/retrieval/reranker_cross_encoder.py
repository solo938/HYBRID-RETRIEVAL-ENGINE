"""
Cross-encoder reranker using BGE-reranker-large
"""
import json
import numpy as np
from pathlib import Path
from sentence_transformers import CrossEncoder, SentenceTransformer

class CrossEncoderReranker:
    def __init__(self, model_name="BAAI/bge-reranker-large"):
        print(f"🔧 Loading cross-encoder: {model_name}...")
        self.model = CrossEncoder(model_name, max_length=512)
        print("  ✅ Cross-encoder loaded")
    
    def rerank(self, query: str, documents: list, top_k: int = 10):
        """Rerank documents using cross-encoder"""
        if not documents:
            return []
        
        # Create query-document pairs
        pairs = [[query, doc["text"]] for doc in documents]
        
        # Get relevance scores
        scores = self.model.predict(pairs)
        
        # Sort by score
        reranked = sorted(
            zip(documents, scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {"chunk_id": doc["chunk_id"], "score": float(score)}
            for doc, score in reranked[:top_k]
        ]

class DenseRetrieverWithReranker:
    """Dense retriever + cross-encoder reranking"""
    
    def __init__(self):
        print("🔧 Initializing Dense Retriever with Reranker...")
        
        # Dense retriever
        self.dense_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        
        # Cross-encoder reranker
        self.reranker = CrossEncoderReranker()
        
        self.documents = []
        self.dense_embeddings = []
        self._load_documents()
    
    def _load_documents(self):
        """Load documents from golden dataset"""
        path = Path("app/evaluation/datasets/goldens/relevant_docs.json")
        with open(path) as f:
            data = json.load(f)
        
        seen = {}
        for item in data:
            context = item.get("context_preview", "")
            for chunk_id in item.get("chunk_ids", []):
                if chunk_id and context and chunk_id not in seen:
                    seen[chunk_id] = context
        
        print(f"  Indexing {len(seen)} documents...")
        
        self.documents = [{"chunk_id": cid, "text": text} for cid, text in seen.items()]
        
        # Generate dense embeddings
        texts = [doc["text"] for doc in self.documents]
        print("  Generating dense embeddings...")
        self.dense_embeddings = self.dense_model.encode(texts, normalize_embeddings=True)
        
        print(f"  ✅ Indexed {len(self.documents)} documents")
    
    def _dense_search(self, query: str, k: int = 50):
        """Initial dense retrieval"""
        q_emb = self.dense_model.encode(query, normalize_embeddings=True)
        scores = self.dense_embeddings @ q_emb
        top_idx = np.argsort(scores)[-k:][::-1]
        
        return [
            {"chunk_id": self.documents[i]["chunk_id"], 
             "text": self.documents[i]["text"],
             "score": float(scores[i])}
            for i in top_idx
        ]
    
    def search(self, query: str, limit: int = 10):
        """Retrieve with reranking"""
        # Initial retrieval (get top 50)
        initial_results = self._dense_search(query, k=50)
        
        # Rerank with cross-encoder
        reranked = self.reranker.rerank(query, initial_results, top_k=limit)
        
        return reranked

# Test
if __name__ == "__main__":
    retriever = DenseRetrieverWithReranker()
    
    test_queries = [
        "In what country is Normandy located?",
        "What is hybrid search?",
    ]
    
    print("\n🔍 Testing dense + reranker:")
    for query in test_queries:
        print(f"\n  Query: {query}")
        results = retriever.search(query, limit=3)
        for r in results:
            print(f"    - {r['chunk_id']}: {r['score']:.4f}")
