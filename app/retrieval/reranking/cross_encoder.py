"""Cross-encoder reranker for precise relevance scoring of (query, chunk) pairs."""
from typing import List, Dict, Any, Optional
from sentence_transformers import CrossEncoder


class CrossEncoderReranker:
    """
    Reranks retrieved chunks using a cross-encoder model.
    Input: query + list of chunks
    Output: reranked list with relevance scores (new dicts, no mutation).
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = "cpu",  # or "cuda"
        batch_size: int = 32,
    ):
        """
        Initialize cross-encoder reranker.

        Args:
            model_name: Hugging Face cross-encoder model name.
            device: "cpu" or "cuda"
            batch_size: Batch size for inference.
        """
        self.model = CrossEncoder(model_name, device=device)
        self.batch_size = batch_size

    def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rerank chunks based on their relevance to the query.

        Args:
            query: User query string.
            chunks: List of result dicts from hybrid retriever.
                    Each dict must contain "content" field.
            top_k: Number of chunks to return after reranking.
            min_score: Minimum rerank score threshold (filter out low scores).

        Returns:
            List of new dicts (no mutation of input), each enriched with:
            {
                ... (original fields),
                "rerank_score": float,
                "original_rank": int,
            }
        """
        if not chunks:
            return []

        # Prepare (query, chunk_text) pairs
        pairs = [(query, chunk["content"]) for chunk in chunks]

        # Get relevance scores (higher = more relevant)
        scores = self.model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
        )

        # Create new dicts (no mutation)
        enriched_chunks = []
        for idx, chunk in enumerate(chunks):
            new_chunk = dict(chunk)  # shallow copy (enough for primitive values)
            new_chunk["rerank_score"] = float(scores[idx])
            new_chunk["original_rank"] = idx + 1
            enriched_chunks.append(new_chunk)

        # Sort by rerank score descending
        reranked = sorted(enriched_chunks, key=lambda x: x["rerank_score"], reverse=True)

        # Optional score threshold filtering
        if min_score is not None:
            reranked = [r for r in reranked if r["rerank_score"] >= min_score]

        # Truncate if top_k specified
        if top_k is not None and top_k > 0:
            reranked = reranked[:top_k]

        return reranked


# Example usage
if __name__ == "__main__":
    # Dummy chunks (as returned by hybrid retriever)
    sample_chunks = [
        {"chunk_id": "doc1", "content": "Neural networks require large amounts of data."},
        {"chunk_id": "doc2", "content": "Deep learning is a subset of machine learning."},
        {"chunk_id": "doc3", "content": "The sky is blue because of Rayleigh scattering."},
    ]

    reranker = CrossEncoderReranker()
    query = "What is deep learning?"
    reranked = reranker.rerank(query, sample_chunks, top_k=2)

    for r in reranked:
        print(f"Score: {r['rerank_score']:.4f} | {r['content'][:60]}...")