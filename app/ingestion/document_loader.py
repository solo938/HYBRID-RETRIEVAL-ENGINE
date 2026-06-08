"""
Orchestrates the complete ingestion pipeline:
File → Parser → Chunker → Embedder → Ready-to-index documents.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.ingestion.parsers.pdf_parser import parse_pdf
from app.ingestion.chunking.recursive_chunker import RAGChunkingPipeline, Chunk
from app.ingestion.embeddings.bge_embedder import BGEEmbedder


def load_document(
    file_path: str | Path,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    embedder: Optional[BGEEmbedder] = None,
    embedding_batch_size: int = 32
) -> List[Dict[str, Any]]:
    """
    Load a document, parse, chunk, embed, and return ready-to-index items.

    Args:
        file_path: Path to the document (PDF only for now)
        chunk_size: Target characters per chunk
        chunk_overlap: Overlap between consecutive chunks
        embedder: Optional BGEEmbedder instance (if None, creates a default one)
        embedding_batch_size: Batch size for encoding (only if embedder not provided)

    Returns:
        List of dicts, each containing:
        {
            "chunk_id": str,
            "content": str,
            "embedding": List[float],
            "metadata": dict,
            "page_number": Optional[int]
        }
    """
    file_path = Path(file_path)
    
    # 1. Parse PDF → text + metadata
    parsed = parse_pdf(file_path)
    raw_text = parsed["text"]
    source_metadata = parsed["metadata"]
    
    # 2. Chunk the text
    chunker = RAGChunkingPipeline(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        min_chunk_size=100,
        document_type="prose"   # PDFs are typically prose
    )
    chunks: List[Chunk] = chunker.chunk(
        text=raw_text,
        source_metadata=source_metadata
        # page_numbers not yet supplied; parser doesn't return char->page map.
        # We'll improve later. For now, page_number remains None.
    )
    
    # 3. Embed chunks
    if embedder is None:
        embedder = BGEEmbedder(batch_size=embedding_batch_size)
    embeddings = embedder.encode(chunks)
    
    # 4. Build final documents ready for indexing
    documents = []
    for chunk, embedding in zip(chunks, embeddings):
        doc = {
            "chunk_id": chunk.chunk_id,
            "content": chunk.content,
            "embedding": embedding,
            "metadata": chunk.metadata,
            "page_number": chunk.page_number,
        }
        documents.append(doc)
    
    return documents


# Example usage (test with a real PDF)
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python document_loader.py <path_to_pdf>")
        sys.exit(1)
    
    docs = load_document(sys.argv[1], chunk_size=500, chunk_overlap=50)
    print(f"Loaded {len(docs)} chunks")
    if docs:
        print(f"First chunk preview: {docs[0]['content'][:200]}...")
        print(f"Embedding dimension: {len(docs[0]['embedding'])}")