"""Citation models for grounded answers."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Citation:
    """A reference to a source document or chunk."""
    citation_id: int
    chunk_id: str
    document_id: str
    source_uri: str
    page_number: Optional[int] = None

    def format_inline(self) -> str:
        return f"[{self.citation_id}]"

    def format_appendix(self) -> str:
        page = f" p.{self.page_number}" if self.page_number else ""
        return f"[{self.citation_id}] {self.source_uri}{page}"