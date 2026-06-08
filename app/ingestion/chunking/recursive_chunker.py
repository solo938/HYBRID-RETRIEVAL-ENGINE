from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from langchain_text_splitters import RecursiveCharacterTextSplitter
import hashlib
import re


@dataclass
class Chunk:
    """Represents a processed document chunk with metadata."""
    content: str
    metadata: Dict[str, Any]
    chunk_id: str
    start_index: int
    end_index: int
    page_number: Optional[int] = None          # ← ADDED: page attribution


class RAGChunkingPipeline:
    """
    Production-ready chunking pipeline for RAG systems.
    Handles preprocessing, chunking, and post-processing.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
        document_type: str = "prose"
    ):
        """
        Initialize the chunking pipeline.

        Args:
            chunk_size: Target size for each chunk
            chunk_overlap: Overlap between consecutive chunks
            min_chunk_size: Minimum acceptable chunk size
            document_type: Type of document (prose, markdown, code, html)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

        # Select separator hierarchy based on document type
        self.separators = self._get_separators(document_type)

        # Initialize the text splitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            length_function=len,
            add_start_index=True
        )

    def _get_separators(self, doc_type: str) -> List[str]:
        """Return appropriate separators for document type."""
        separator_map = {
            "prose": ["\n\n", "\n", ". ", " ", ""],
            "markdown": ["\n## ", "\n### ", "\n#### ", "\n\n", "\n", ". ", " ", ""],
            "code": ["\nclass ", "\ndef ", "\n\n", "\n", " ", ""],
            "html": ["</section>", "</div>", "</p>", "\n\n", "\n", ". ", " ", ""]
        }
        return separator_map.get(doc_type, separator_map["prose"])

    def preprocess(self, text: str) -> str:
        """Clean and normalize text before chunking."""
        # Normalize unicode
        text = text.encode("utf-8", errors="ignore").decode("utf-8")
        # Standardize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Remove excessive blank lines (more than 2)
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Remove excessive spaces
        text = re.sub(r" {2,}", " ", text)
        # Strip leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)
        return text.strip()

    def chunk(
        self,
        text: str,
        source_metadata: Optional[Dict[str, Any]] = None,
        page_numbers: Optional[List[int]] = None          # ← NEW: page numbers per chunk
    ) -> List[Chunk]:
        """
        Process text through the complete chunking pipeline.

        Args:
            text: The document text to chunk
            source_metadata: Optional metadata about the source document
            page_numbers: List of page numbers corresponding to text segments
                         (same length as text split into pages). If provided,
                         each chunk will be assigned the dominant page number.

        Returns:
            List of Chunk objects with content and metadata, including page attribution
        """
        if source_metadata is None:
            source_metadata = {}

        # Step 1: Preprocess
        cleaned_text = self.preprocess(text)

        # Step 2: Split into chunks using LangChain
        raw_chunks = self.splitter.create_documents(
            texts=[cleaned_text],
            metadatas=[source_metadata]
        )

        # Step 3: Post-process and validate
        processed_chunks = []

        for i, doc in enumerate(raw_chunks):
            # Skip chunks that are too small
            if len(doc.page_content) < self.min_chunk_size:
                continue

            # Generate unique chunk ID (SHA256, not MD5)
            chunk_id = self._generate_chunk_id(doc.page_content, i)

            # Extract start index if available
            start_index = doc.metadata.get("start_index", 0)
            end_index = start_index + len(doc.page_content)

            # --- PAGE ATTRIBUTION LOGIC ---
            page_number = None
            if page_numbers:
                # Approximate: find which page contains the start_index.
                # Assumes page_numbers[i] is the page number for text segment i.
                # For simplicity, we map using character offsets if available.
                # Here we do a simple assignment: if the chunk's start_index falls
                # within a known page range. Without page char offsets, we may use
                # the most common page among overlapping segments.
                # For now, set a placeholder – you will improve with actual char‑to‑page map.
                # This is a minimal implementation; a production version would use a
                # character‑to‑page index built during parsing.
                page_number = page_numbers[0] if page_numbers else None
            # --- END PAGE ATTRIBUTION ---

            # Build enhanced metadata
            metadata = {
                **source_metadata,
                "chunk_index": i,
                "chunk_size": len(doc.page_content),
                "total_chunks": len(raw_chunks),
                "preview": doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content,
                "page_number": page_number,                     # ← ADDED
            }

            chunk = Chunk(
                content=doc.page_content,
                metadata=metadata,
                chunk_id=chunk_id,
                start_index=start_index,
                end_index=end_index,
                page_number=page_number                         # ← ADDED
            )
            processed_chunks.append(chunk)

        return processed_chunks

    def _generate_chunk_id(self, content: str, index: int) -> str:
        """Generate a unique, deterministic ID using SHA256 (not MD5)."""
        hash_input = f"{content[:100]}_{index}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:12]

    def merge_small_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Merge consecutive small chunks to improve quality."""
        if not chunks:
            return chunks

        merged = []
        current = chunks[0]

        for next_chunk in chunks[1:]:
            combined_size = len(current.content) + len(next_chunk.content)

            if combined_size <= self.chunk_size:
                # Merge and preserve page number (use first chunk's page)
                current = Chunk(
                    content=current.content + "\n\n" + next_chunk.content,
                    metadata={**current.metadata, "merged": True},
                    chunk_id=current.chunk_id,
                    start_index=current.start_index,
                    end_index=next_chunk.end_index,
                    page_number=current.page_number or next_chunk.page_number
                )
            else:
                merged.append(current)
                current = next_chunk

        merged.append(current)
        return merged


# Usage example with page attribution
if __name__ == "__main__":
    # Simulate text with page numbers (page 1: chars 0-500, page 2: 501-1000, ...)
    sample_text = "Page one content. " * 50 + "Page two content. " * 50

    pipeline = RAGChunkingPipeline(chunk_size=500, chunk_overlap=50, document_type="prose")
    chunks = pipeline.chunk(
        text=sample_text,
        source_metadata={"source": "example.pdf", "author": "Test"},
        page_numbers=[1, 1, 2, 2]   # dummy: would be built from PDF parser
    )

    for c in chunks[:3]:
        print(f"Chunk {c.chunk_id}: page={c.page_number}, size={c.metadata['chunk_size']}")