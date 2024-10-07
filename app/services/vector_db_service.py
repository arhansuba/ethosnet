from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.core.config import settings

class VectorDBService:
    def __init__(self):
        self.client = QdrantClient(url=settings.VECTOR_DB_URL, api_key=settings.VECTOR_DB_API_KEY)

    async def create_collection(self, collection_name: str, vector_size: int):
        """
        Create a new collection in the vector database.
        """
        self.client.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )

    async def add_item(self, collection_name: str, id: str, vector: List[float], payload: Dict[str, Any]):
        """
        Add a single item to the specified collection.
        """
        self.client.upsert(
            collection_name=collection_name,
            points=[models.PointStruct(id=id, vector=vector, payload=payload)],
        )

    async def add_items(self, collection_name: str, items: List[Dict[str, Any]]):
        """
        Add multiple items to the specified collection.
        """
        points = [
            models.PointStruct(id=item['id'], vector=item['vector'], payload=item['payload'])
            for item in items
        ]
        self.client.upsert(collection_name=collection_name, points=points)

    async def search_similar(
        self, 
        collection_name: str, 
        query_vector: List[float], 
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar items in the specified collection.
        """
        search_result = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold
        )
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in search_result
        ]

    async def get_item(self, collection_name: str, id: str) -> Dict[str, Any]:
        """
        Retrieve a specific item by its ID.
        """
        result = self.client.retrieve(collection_name=collection_name, ids=[id])
        if result:
            return {"id": result[0].id, "payload": result[0].payload}
        return None

    async def update_item(self, collection_name: str, id: str, payload: Dict[str, Any]):
        """
        Update the payload of a specific item.
        """
        self.client.set_payload(
            collection_name=collection_name,
            points=[id],
            payload=payload
        )

    async def delete_item(self, collection_name: str, id: str):
        """
        Delete a specific item from the collection.
        """
        self.client.delete(collection_name=collection_name, points_selector=models.PointIdsList(points=[id]))

    async def search(
        self, 
        collection_name: str, 
        query_filter: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for items based on filter conditions.
        """
        filter_params = models.Filter(**query_filter) if query_filter else None
        result = self.client.scroll(
            collection_name=collection_name,
            scroll_filter=filter_params,
            limit=limit,
            offset=offset,
        )
        return [{"id": item.id, "payload": item.payload} for item in result[0]]

    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get information about a specific collection.
        """
        return self.client.get_collection(collection_name=collection_name).dict()

    async def list_collections(self) -> List[str]:
        """
        List all collections in the database.
        """
        collections = self.client.get_collections()
        return [collection.name for collection in collections.collections]

    async def delete_collection(self, collection_name: str):
        """
        Delete a collection from the database.
        """
        self.client.delete_collection(collection_name=collection_name)

    async def get_collection_size(self, collection_name: str) -> int:
        """
        Get the number of items in a collection.
        """
        return self.client.get_collection(collection_name=collection_name).points_count

    async def create_payload_index(self, collection_name: str, field_name: str, field_schema: Dict[str, Any]):
        """
        Create an index on a payload field for faster filtering.
        """
        self.client.create_payload_index(
            collection_name=collection_name,
            field_name=field_name,
            field_schema=models.PayloadSchemaType(**field_schema)
        )