"""FastAPI dependency injection for shared services."""
from functools import lru_cache
from app.retrieval.hybrid_retriever import HybridRetriever
from app.llm.providers.local_provider import LocalLLMProvider  # Changed
from app.core.config import settings

_retriever = None
_llm = None

def get_retriever():
    global _retriever
    if _retriever is None:
        try:
            _retriever = HybridRetriever()
        except Exception as e:
            print(f"Warning: Failed to initialize retriever: {e}")
            _retriever = None
    return _retriever

def get_llm():
    global _llm
    if _llm is None:
        try:
            # Use local free model
            _llm = LocalLLMProvider(model="mistral")  # Change model name as needed
        except Exception as e:
            print(f"Warning: Failed to initialize LLM: {e}")
            _llm = None
    return _llm

def get_rag_pipeline():
    retriever = get_retriever()
    llm = get_llm()
    if retriever is None or llm is None:
        return None
    from app.generation.rag_pipeline import RAGPipeline
    return RAGPipeline(retriever=retriever, llm=llm)