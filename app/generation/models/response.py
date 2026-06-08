"""Response models for grounded answers."""
from dataclasses import dataclass
from typing import List

from .citations import Citation


@dataclass
class GroundedAnswer:
    """Final grounded answer with citations."""
    answer: str
    citations: List[Citation]
    grounded: bool
    total_tokens: int = 0