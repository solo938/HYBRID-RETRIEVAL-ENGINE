"""BM25 sparse lexical indexer using rank-bm25."""
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi

from app.core.config import settings


class BM25Indexer:
    """
    BM25 lexical retrieval index.
    Tokenizes chunks and provides search capabilities.
    """

    def __init__(self, cache_path: Optional[Path] = None):
        """
        Initialize BM25 indexer.
        If cache_path is None, try settings.BM25_INDEX_PATH; otherwise use a default path.
        """
        if cache_path is None:
            cache_path = settings.BM25_INDEX_PATH
        if cache_path is None:
            # Set a default path in the data directory
            cache_path = Path("data/bm25_index.pkl")
        self.cache_path = cache_path
        self.index: Optional[BM25Okapi] = None
        self.documents: List[Dict[str, Any]] = []

    def index_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Build BM25 index from a list of documents (output of document_loader).
        """
        if not documents:
            return

        self.documents = documents
        tokenized_corpus = [self._tokenize(doc["content"]) for doc in documents]
        self.index = BM25Okapi(tokenized_corpus)
        print(f"Built BM25 index with {len(documents)} documents")
        if self.cache_path:
            self.save()

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Retrieve top-k chunks using BM25."""
        if not self.index:
            raise ValueError("BM25 index not built. Call index_documents() first.")
        tokenized_query = self._tokenize(query)
        scores = self.index.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        results = []
        for idx in top_indices:
            doc = self.documents[idx]
            results.append({
                "chunk_id": doc["chunk_id"],
                "content": doc["content"],
                "score": float(scores[idx]),
                "payload": doc.get("metadata", {}),
            })
        return results

    def _tokenize(self, text: str) -> List[str]:
        return text.lower().split()

    def save(self) -> None:
        """Save BM25 index and documents to disk."""
        if not self.cache_path:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "wb") as f:
            pickle.dump({
                "index": self.index,
                "documents": self.documents,
            }, f)
        print(f"Saved BM25 index to {self.cache_path}")

    def load(self) -> bool:
        """Load BM25 index and documents from disk. Returns True if loaded."""
        if not self.cache_path or not self.cache_path.exists():
            return False
        with open(self.cache_path, "rb") as f:
            data = pickle.load(f)
            self.index = data["index"]
            self.documents = data["documents"]
        print(f"Loaded BM25 index from {self.cache_path} ({len(self.documents)} docs)")
        return True


# Example usage
if __name__ == "__main__":
    from app.ingestion.document_loader import load_document
    docs = load_document("sample.pdf", chunk_size=500, chunk_overlap=50)
    bm25 = BM25Indexer(cache_path=Path("data/bm25_index.pkl"))
    bm25.index_documents(docs)
    results = bm25.search("machine learning", top_k=3)
    for r in results:
        print(f"Score: {r['score']:.2f} | {r['content'][:100]}...")