"""ACL models for document‑level security."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class ACLContext:
    """User's access control context at query time."""
    user_id: str
    groups: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)


@dataclass
class ACLDocument:
    """ACL information attached to each document/chunk during indexing."""
    users: List[str] = field(default_factory=list)   # explicit user IDs
    groups: List[str] = field(default_factory=list)  # group names
    roles: List[str] = field(default_factory=list)   # role names
    public: bool = False