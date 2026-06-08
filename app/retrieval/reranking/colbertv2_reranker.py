# retrieval/reranking/colbertv2_reranker.py
"""
ColBERTv2 late interaction reranking
Requires: pip install ragatouille
"""
from typing import List, Tuple, Dict, Any
import numpy as np
from ragatouille import RAGPretrainedModel

class ColBERTv2Reranker:
    """Production ColBERTv2 reranker with late interaction"""
    
    def __init__(self, model_name: str = "colbert-ir/colbertv2.0", use_gpu: bool = False):
        self.model = RAGPretrainedModel.from_pretrained(model_name)
        self.use_gpu = use_gpu
        self._cache = {}
    
    def rerank(self, query: str, documents: List[str], top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Rerank documents using ColBERTv2 late interaction
        
        Args:
            query: User query
            documents: List of document texts
            top_k: Number of documents to return
        
        Returns:
            List of (document, score) tuples sorted by relevance
        """
        # Use ColBERT's built-in reranking
        results = self.model.rerank(
            query=query,
            documents=documents,
            k=top_k,
            max_docs=len(documents)
        )
        
        return [(r["content"], r["score"]) for r in results]
    
    def encode_query(self, query: str) -> np.ndarray:
        """Encode query for late interaction matching"""
        return self.model.encode(query, is_query=True)
    
    def encode_document(self, document: str) -> np.ndarray:
        """Encode document for late interaction matching"""
        return self.model.encode(document, is_query=False)
    
    def maxsim_score(self, query_embedding: np.ndarray, doc_embedding: np.ndarray) -> float:
        """Compute MaxSim score between query and document"""
        # Token-level similarity
        similarity = np.dot(query_embedding, doc_embedding.T)
        # Max over document tokens for each query token
        max_sim = np.max(similarity, axis=1)
        # Sum over query tokens
        return np.sum(max_sim)
    
    def batch_rerank(self, queries: List[str], documents_list: List[List[str]], top_k: int = 10) -> List[List[Tuple[str, float]]]:
        """Rerank multiple queries in batch"""
        results = []
        for query, documents in zip(queries, documents_list):
            results.append(self.rerank(query, documents, top_k))
        return results

# Integration with existing pipeline
class HybridRetrieverWithColBERT:
    """Hybrid retriever with ColBERTv2 reranking"""
    
    def __init__(self):
        self.colbert = ColBERTv2Reranker()
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        # Step 1: Initial hybrid retrieval (fast)
        initial_results = self.hybrid_search(query, limit=50)
        
        # Step 2: ColBERT reranking (accurate)
        documents = [r['text'] for r in initial_results]
        reranked = self.colbert.rerank(query, documents, top_k=top_k)
        
        # Step 3: Return with scores
        return [
            {'text': doc, 'score': score, 'source': 'colbert_reranked'}
            for doc, score in reranked
        ]