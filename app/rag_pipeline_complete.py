"""
Complete RAG Pipeline with Query → Retrieval → Reranking → Generation
Includes: citations, cost tracking, latency monitoring
"""
import json
import time
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import numpy as np

from sentence_transformers import SentenceTransformer, CrossEncoder

@dataclass
class RetrievedDocument:
    """Document retrieved from search"""
    chunk_id: str
    content: str
    score: float
    metadata: Dict = field(default_factory=dict)

@dataclass 
class GenerationResult:
    """LLM generation result with citations"""
    answer: str
    citations: List[Dict]
    tokens_used: int
    latency_ms: float
    cost_usd: float

class CompleteRAGPipeline:
    """End-to-end RAG pipeline with all features"""
    
    def __init__(self):
        print("🚀 Initializing Complete RAG Pipeline...")
        
        # Load models
        self.dense_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)
        
        # Load documents
        self.documents = []
        self.embeddings = []
        self._load_documents()
        
        # Setup metrics
        self.metrics = {
            "queries_processed": 0,
            "total_latency_ms": 0,
            "total_cost_usd": 0,
            "avg_recall": 0
        }
        
        print(f"✅ Pipeline ready with {len(self.documents)} documents")
    
    def _load_documents(self):
        """Load documents from golden dataset"""
        goldens = Path("app/evaluation/datasets/goldens")
        
        with open(goldens / "questions.json") as f:
            questions = json.load(f)
        
        # Build document index
        for q in questions:
            if q.get("context"):
                self.documents.append({
                    "chunk_id": q["id"],
                    "content": q["context"],
                    "question": q["text"],
                    "metadata": {
                        "domain": q.get("domain", "general"),
                        "difficulty": q.get("difficulty", "medium")
                    }
                })
        
        # Generate embeddings
        texts = [d["content"] for d in self.documents]
        self.embeddings = self.dense_model.encode(texts, normalize_embeddings=True)
    
    def retrieve(self, query: str, top_k: int = 50) -> List[RetrievedDocument]:
        """Initial dense retrieval"""
        q_emb = self.dense_model.encode(query, normalize_embeddings=True)
        scores = self.embeddings @ q_emb
        top_idx = np.argsort(scores)[-top_k:][::-1]
        
        return [
            RetrievedDocument(
                chunk_id=self.documents[i]["chunk_id"],
                content=self.documents[i]["content"],
                score=float(scores[i]),
                metadata=self.documents[i].get("metadata", {})
            )
            for i in top_idx
        ]
    
    def rerank(self, query: str, documents: List[RetrievedDocument], top_k: int = 10) -> List[RetrievedDocument]:
        """Rerank documents using cross-encoder"""
        if not documents:
            return []
        
        pairs = [[query, doc.content] for doc in documents]
        scores = self.reranker.predict(pairs)
        
        for doc, score in zip(documents, scores):
            doc.score = float(score)
        
        reranked = sorted(documents, key=lambda x: x.score, reverse=True)
        return reranked[:top_k]
    
    def generate_answer(self, query: str, documents: List[RetrievedDocument]) -> GenerationResult:
        """Generate answer with citations using LLM"""
        start_time = time.time()
        
        # Build context with citations
        context_parts = []
        citations = []
        
        for i, doc in enumerate(documents, 1):
            citation_id = f"[{i}]"
            context_parts.append(f"{citation_id} {doc.content}")
            citations.append({
                "id": i,
                "citation": citation_id,
                "chunk_id": doc.chunk_id,
                "relevance_score": doc.score
            })
        
        context = "\n\n".join(context_parts)
        
        # Simple prompt (in production, use actual LLM)
        prompt = f"""Answer the question based ONLY on the provided context.

Context:
{context}

Question: {query}

Answer the question accurately. Cite sources using their numbers like [1], [2].
If the answer cannot be found in the context, say "I cannot answer based on the provided context."

Answer:"""
        
        # Simulate LLM response (replace with actual OpenAI/Anthropic call)
        # For demo, extract answer from most relevant document
        answer = self._simulate_llm_response(query, documents)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Estimate tokens and cost (GPT-3.5 approximate)
        tokens_used = len(prompt.split()) + len(answer.split())
        cost_usd = tokens_used * 0.002 / 1000  # $0.002 per 1K tokens
        
        return GenerationResult(
            answer=answer,
            citations=citations,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            cost_usd=cost_usd
        )
    
    def _simulate_llm_response(self, query: str, documents: List[RetrievedDocument]) -> str:
        """Simulate LLM response (replace with real LLM)"""
        if not documents:
            return "I cannot answer based on the provided context."
        
        # Extract answer from the most relevant document
        best_doc = documents[0]
        
        # Try to extract a sentence that answers the question
        sentences = best_doc.content.split('.')
        for sentence in sentences:
            if any(word in query.lower() for word in sentence.lower().split()[:5]):
                return f"{sentence.strip()}. [1]"
        
        # Fallback to first sentence
        return f"{sentences[0].strip()} [1]"
    
    def query(self, question: str, verbose: bool = True) -> Dict[str, Any]:
        """Complete RAG pipeline: Query → Retrieve → Rerank → Generate"""
        start_time = time.time()
        
        if verbose:
            print(f"\n🔍 Processing: {question}")
        
        # Step 1: Retrieve
        retrieval_start = time.time()
        retrieved = self.retrieve(question, top_k=50)
        retrieval_latency = (time.time() - retrieval_start) * 1000
        
        # Step 2: Rerank
        rerank_start = time.time()
        reranked = self.rerank(question, retrieved, top_k=5)
        rerank_latency = (time.time() - rerank_start) * 1000
        
        # Step 3: Generate answer
        generation_result = self.generate_answer(question, reranked)
        
        total_latency = (time.time() - start_time) * 1000
        
        # Update metrics
        self.metrics["queries_processed"] += 1
        self.metrics["total_latency_ms"] += total_latency
        self.metrics["total_cost_usd"] += generation_result.cost_usd
        
        result = {
            "question": question,
            "answer": generation_result.answer,
            "citations": generation_result.citations,
            "retrieved_documents": len(retrieved),
            "reranked_documents": len(reranked),
            "latency_ms": {
                "retrieval": retrieval_latency,
                "reranking": rerank_latency,
                "generation": generation_result.latency_ms,
                "total": total_latency
            },
            "cost_usd": generation_result.cost_usd,
            "tokens_used": generation_result.tokens_used
        }
        
        if verbose:
            print(f"✅ Answer generated in {total_latency:.0f}ms (${generation_result.cost_usd:.6f})")
            print(f"📖 Answer: {generation_result.answer[:200]}...")
        
        return result
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get pipeline metrics"""
        if self.metrics["queries_processed"] == 0:
            return self.metrics
        
        return {
            **self.metrics,
            "avg_latency_ms": self.metrics["total_latency_ms"] / self.metrics["queries_processed"],
            "avg_cost_per_query_usd": self.metrics["total_cost_usd"] / self.metrics["queries_processed"]
        }

# Test the pipeline
if __name__ == "__main__":
    pipeline = CompleteRAGPipeline()
    
    test_queries = [
        "In what country is Normandy located?",
        "What is hybrid search?",
        "How do the Normans relate to Normandy?"
    ]
    
    print("\n" + "="*60)
    print("🧪 Testing Complete RAG Pipeline")
    print("="*60)
    
    for query in test_queries:
        result = pipeline.query(query)
        
    print("\n📊 Pipeline Metrics:")
    metrics = pipeline.get_metrics()
    for k, v in metrics.items():
        print(f"  {k}: {v}")
