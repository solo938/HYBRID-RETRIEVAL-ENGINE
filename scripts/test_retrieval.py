# scripts/test_retrieval.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.retrieval.hybrid_retriever import HybridRetriever

print("Initializing retriever...")
retriever = HybridRetriever()

print("Running retrieval...")
result = retriever.retrieve("What is Retrieval Augmented Generation?", top_k=3)

print(f"Result type: {type(result)}")
print(f"Result has 'results' attribute: {hasattr(result, 'results')}")
print(f"Results count: {len(result.results)}")

print("\nFirst chunk details:")
if result.results:
    chunk = result.results[0]
    print(f"  chunk_id: {chunk.chunk_id}")
    print(f"  content preview: {chunk.content[:100]}")
    print(f"  score_breakdown: {chunk.score_breakdown}")
    print(f"  type: {type(chunk)}")
else:
    print("No results returned")