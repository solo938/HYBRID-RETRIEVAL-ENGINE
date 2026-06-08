"""Qdrant vector indexer for storing and retrieving chunk embeddings."""
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from app.core.config import settings


class VectorIndexer:
    """Handles collection creation, upsert, and similarity search in Qdrant."""

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: Optional[str] = None,
        vector_size: Optional[int] = None,
    ):
        self.url = url or settings.QDRANT_URL
        self.api_key = api_key or settings.QDRANT_API_KEY
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self.vector_size = vector_size or settings.EMBEDDING_DIMENSION

        self.client = QdrantClient(
            url=self.url,
            api_key=self.api_key,
            timeout=60.0,
        )

    def _to_uuid(self, chunk_id: str) -> str:
        """Convert any string to a valid UUID format."""
        # Use UUID5 to create a deterministic UUID from the chunk_id
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))

    def create_collection(self, force_recreate: bool = False) -> None:
        """Create a new collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
        except Exception as e:
            print(f"Warning: Could not check collections: {e}")
            exists = False

        if force_recreate and exists:
            try:
                self.client.delete_collection(self.collection_name)
                print(f"Deleted existing collection '{self.collection_name}'")
            except Exception as e:
                print(f"Warning: Could not delete collection: {e}")
            exists = False

        if not exists:
            try:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE,
                    ),
                )
                print(f"Created collection '{self.collection_name}' (dim={self.vector_size})")
            except Exception as e:
                print(f"Warning: Could not create collection: {e}")
        else:
            print(f"Collection '{self.collection_name}' already exists")

    def upsert_documents(self, documents: List[Dict[str, Any]], batch_size: int = 50) -> None:
        """Insert or update a batch of documents in the vector index."""
        if not documents:
            print("No documents to upsert")
            return

        points = []
        for doc in documents:
            # Convert string ID to UUID
            point_id = self._to_uuid(doc["chunk_id"])
            
            payload = {
                "chunk_id": doc["chunk_id"],  # Store original ID in payload
                "content": doc["content"],
                "metadata": doc.get("metadata", {}),
                "page_number": doc.get("page_number"),
                "document_id": doc.get("document_id"),
                "source_uri": doc.get("source_uri"),
                "acl_users": doc.get("acl_users", []),
                "acl_groups": doc.get("acl_groups", []),
            }
            points.append(
                PointStruct(
                    id=point_id,
                    vector=doc["embedding"],
                    payload=payload,
                )
            )

        # Upsert in batches
        total = len(points)
        for i in range(0, total, batch_size):
            batch = points[i:i+batch_size]
            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch,
                )
                batch_num = i // batch_size + 1
                total_batches = (total + batch_size - 1) // batch_size
                print(f"Upserted batch {batch_num}/{total_batches} ({len(batch)} points)")
            except Exception as e:
                print(f"Error upserting batch {i//batch_size + 1}: {e}")
                raise

        print(f"Successfully upserted {total} points into '{self.collection_name}'")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve top-k most similar chunks to the query embedding."""
        # Build search parameters
        search_kwargs = {
            "collection_name": self.collection_name,
            "limit": top_k,
            "with_payload": True,
        }
        
        # Use query_points for newer Qdrant versions, fall back to search for older
        try:
            # Try the newer API (Qdrant v1.7+)
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=top_k,
                score_threshold=score_threshold,
            ).points
        except (AttributeError, TypeError):
            # Fall back to older API
            search_kwargs["query_vector"] = query_embedding
            if score_threshold is not None:
                search_kwargs["score_threshold"] = score_threshold
            if filters is not None:
                search_kwargs["query_filter"] = filters
            results = self.client.search(**search_kwargs)

        hits = []
        for hit in results:
            hits.append({
                "chunk_id": hit.payload.get("chunk_id", str(hit.id)),
                "content": hit.payload.get("content", ""),
                "score": hit.score,
                "payload": hit.payload,
            })
        return hits

    def delete_collection(self) -> None:
        """Permanently delete the entire collection."""
        try:
            self.client.delete_collection(self.collection_name)
            print(f"Deleted collection '{self.collection_name}'")
        except Exception as e:
            print(f"Warning: Could not delete collection: {e}")


# Example usage
if __name__ == "__main__":
    from app.ingestion.document_loader import load_document
    import random

    # Path to a sample PDF
    sample_pdf = "sample.pdf"
    docs = load_document(sample_pdf, chunk_size=500, chunk_overlap=50)

    indexer = VectorIndexer()
    indexer.create_collection(force_recreate=True)
    indexer.upsert_documents(docs, batch_size=20)

    dummy_embedding = [random.random() for _ in range(settings.EMBEDDING_DIMENSION)]
    results = indexer.search(dummy_embedding, top_k=3)
    for r in results:
        print(f"Score: {r['score']:.4f} | Content: {r['content'][:80]}...")