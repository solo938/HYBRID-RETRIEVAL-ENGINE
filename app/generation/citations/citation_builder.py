"""Build citations from retrieved chunks."""
from typing import List, Tuple
from app.core.models.retrieval import RetrievedChunk
from app.generation.models.citations import Citation


class CitationBuilder:
    """Assign citation IDs to chunks and build reference lists."""

    def build(self, chunks: List[RetrievedChunk]) -> Tuple[List[Citation], List[RetrievedChunk]]:
        citations = []
        for idx, chunk in enumerate(chunks, start=1):
            citation = Citation(
                citation_id=idx,
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id or "unknown",
                source_uri=chunk.source_uri or "unknown",
                page_number=chunk.page_number,
            )
            citations.append(citation)
            # Attach citation_id to chunk metadata
            chunk.metadata["citation_id"] = idx
        return citations, chunks