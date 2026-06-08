"""Query‑time authorization filtering."""
from app.core.models.security import ACLContext
from app.core.models.retrieval import RetrievedChunk


class AuthorizationFilter:
    """Filter chunks that the user is allowed to see."""

    @staticmethod
    def filter_chunks(chunks: list[RetrievedChunk], acl: ACLContext) -> list[RetrievedChunk]:
        allowed = []
        for chunk in chunks:
            # Public chunks are always allowed
            if chunk.metadata.get("public", False):
                allowed.append(chunk)
                continue
            # Check explicit user ID
            if acl.user_id in chunk.acl_users:
                allowed.append(chunk)
                continue
            # Check groups intersection
            if set(acl.groups).intersection(chunk.acl_groups):
                allowed.append(chunk)
                continue
            # Check roles from metadata
            metadata_roles = chunk.metadata.get("acl_roles", [])
            if isinstance(metadata_roles, list) and set(acl.roles).intersection(metadata_roles):
                allowed.append(chunk)
                continue
        return allowed