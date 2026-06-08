"""BGE embedding model for dense retrieval with batching and normalization."""
from typing import List, Union
from sentence_transformers import SentenceTransformer
import numpy as np

# Import Chunk dataclass from chunking module (assuming relative import)
from ..chunking.recursive_chunker import Chunk


class BGEEmbedder:
    """Minimal BGE embedder with batch encoding and L2 normalization."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        batch_size: int = 32,
        device: str = "cpu"  # or "cuda" if GPU available
    ):
        """
        Initialize the BGE embedding model.

        Args:
            model_name: Hugging Face model name (default: small BGE)
            batch_size: Number of chunks to encode per batch
            device: "cpu" or "cuda"
        """
        self.model = SentenceTransformer(model_name, device=device)
        self.batch_size = batch_size

    def encode(self, chunks: List[Chunk]) -> List[List[float]]:
        """
        Convert a list of Chunks into dense vector embeddings.

        Steps:
        1. Extract text content from each chunk
        2. Encode in batches (memory efficient)
        3. Normalize embeddings (required for BGE + cosine similarity)

        Args:
            chunks: List of Chunk objects (each has .content)

        Returns:
            List of embedding vectors (each as list of floats)
        """
        if not chunks:
            return []

        texts = [chunk.content for chunk in chunks]

        # Encode with batch size and normalization
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,   # CRITICAL for BGE
            show_progress_bar=False      # Keep minimal
        )

        # Convert numpy arrays to standard Python lists
        return embeddings.tolist()

    def encode_single(self, chunk: Chunk) -> List[float]:
        """Encode a single chunk (returns list of floats)."""
        return self.encode([chunk])[0]

    def encode_single_text(self, text: str) -> List[float]:
        """Encode a single text string directly (no Chunk object)."""
        embeddings = self.model.encode(
            [text],
            batch_size=1,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embeddings[0].tolist()


# Example usage (quick test)
if __name__ == "__main__":
    # Create dummy chunks
    from dataclasses import dataclass
    @dataclass
    class DummyChunk:
        content: str
        metadata: dict
        chunk_id: str
        start_index: int
        end_index: int
        page_number: int = None

    chunks = [
        DummyChunk("The quick brown fox jumps over the lazy dog.", {}, "id1", 0, 30),
        DummyChunk("Machine learning is a subset of artificial intelligence.", {}, "id2", 0, 50),
    ]

    embedder = BGEEmbedder(batch_size=2)
    vectors = embedder.encode(chunks)

    print(f"Generated {len(vectors)} embeddings")
    print(f"Vector dimension: {len(vectors[0])}")   # Should be 384 for bge-small
    print(f"First 5 values: {vectors[0][:5]}")

    # Test single text encoding
    single_vector = embedder.encode_single_text("Hello world")
    print(f"Single text embedding dimension: {len(single_vector)}")