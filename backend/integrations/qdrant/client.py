import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import uuid
import logging

logger = logging.getLogger(__name__)

class QdrantConnector:
    def __init__(self):
        self.url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.client = QdrantClient(url=self.url)
        self.vector_size = 1024 # BGE Large size typical

    def ensure_collection(self, collection_name: str):
        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection {collection_name}")

    def upsert_vectors(self, collection_name: str, points: list):
        """points should be a list of dicts with 'vector' and 'payload' keys."""
        qdrant_points = [
            PointStruct(
                id=str(uuid.uuid4()) if 'id' not in p else p['id'], 
                vector=p['vector'], 
                payload=p.get('payload', {})
            )
            for p in points
        ]
        self.client.upsert(
            collection_name=collection_name,
            points=qdrant_points
        )

    def search(self, collection_name: str, query_vector: list, limit: int = 5):
        return self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit
        )

qdrant_connector = QdrantConnector()
