"""Build Qdrant filters from RetrievalFilters and ACL context."""
from typing import Optional, Dict, Any
from app.core.models.filters import RetrievalFilters
from app.core.models.security import ACLContext


class QdrantFilterBuilder:
    """Convert retrieval filters and ACL to Qdrant's payload filter syntax."""

    @staticmethod
    def build(
        filters: Optional[RetrievalFilters] = None,
        acl: Optional[ACLContext] = None,
    ) -> Optional[Dict[str, Any]]:
        """Build a Qdrant 'must' filter clause."""
        must = []

        # Metadata filters
        if filters:
            if filters.document_ids:
                must.append({
                    "key": "document_id",
                    "match": {"any": filters.document_ids}
                })
            if filters.sources:
                must.append({
                    "key": "source_uri",
                    "match": {"any": filters.sources}
                })
            if filters.tags:
                must.append({
                    "key": "metadata.tags",
                    "match": {"any": filters.tags}
                })
            for k, v in filters.metadata.items():
                must.append({
                    "key": f"metadata.{k}",
                    "match": {"value": v}
                })

        # ACL filtering (during retrieval)
        if acl:
            acl_conditions = []
            if acl.user_id:
                acl_conditions.append({
                    "key": "acl_users",
                    "match": {"value": acl.user_id}
                })
            if acl.groups:
                acl_conditions.append({
                    "key": "acl_groups",
                    "match": {"any": acl.groups}
                })
            if acl.roles:
                acl_conditions.append({
                    "key": "acl_roles",
                    "match": {"any": acl.roles}
                })
            acl_conditions.append({
                "key": "metadata.public",
                "match": {"value": True}
            })
            if acl_conditions:
                must.append({"should": acl_conditions})

        return {"must": must} if must else None