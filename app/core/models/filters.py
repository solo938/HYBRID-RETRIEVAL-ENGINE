"""Retrieval filters for metadata and security."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RetrievalFilters:
    """Filtering conditions applied during retrieval."""
    document_ids: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    created_after: Optional[str] = None   # ISO date string
    created_before: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)