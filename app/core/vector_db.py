from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
import numpy as np
import uuid

class VectorDB:
    def __init__(self, url: str, collection_name: str):
        """
        Initialize the VectorDB class.
        
        Args:
            url (str): URL of the Qdrant server.
            collection_name (str): Name of the collection to use.
        """
        self.client = QdrantClient(url)
        self.collection_name = collection_name
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Ensure that the specified collection exists, create it if it doesn't."""
        collections = self.client.get_collections().collections
        if not any(collection.name == self.collection_name for collection in collections):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )

    def add(self, embedding: List[float], content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a new entry to the vector database.
        
        Args:
            embedding (List[float]): The vector embedding of the content.
            content (str): The actual content to be stored.
            metadata (Optional[Dict[str, Any]]): Additional metadata for the entry.
        
        Returns:
            str: The ID of the newly added entry.
        """
        entry_id = str(uuid.uuid4())
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=entry_id,
                    vector=embedding,
                    payload={"content": content, **(metadata or {})}
                )
            ]
        )
        return entry_id

    def get(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an entry by its ID.
        
        Args:
            entry_id (str): The ID of the entry to retrieve.
        
        Returns:
            Optional[Dict[str, Any]]: The retrieved entry or None if not found.
        """
        results = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[entry_id]
        )
        if results:
            return {
                "id": results[0].id,
                "content": results[0].payload.get("content"),
                "metadata": {k: v for k, v in results[0].payload.items() if k != "content"}
            }
        return None

    def search(self, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar entries based on a query vector.
        
        Args:
            query_vector (List[float]): The query vector to search for.
            limit (int): The maximum number of results to return.
        
        Returns:
            List[Dict[str, Any]]: A list of similar entries.
        """
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit
        )
        return [
            {
                "id": result.id,
                "content": result.payload.get("content"),
                "metadata": {k: v for k, v in result.payload.items() if k != "content"},
                "score": result.score
            }
            for result in search_results
        ]

    def update(self, entry_id: str, content: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Update an existing entry in the database.
        
        Args:
            entry_id (str): The ID of the entry to update.
            content (Optional[str]): New content for the entry.
            metadata (Optional[Dict[str, Any]]): New or updated metadata for the entry.
        """
        payload = {}
        if content is not None:
            payload["content"] = content
        if metadata is not None:
            payload.update(metadata)

        self.client.set_payload(
            collection_name=self.collection_name,
            points=[entry_id],
            payload=payload
        )

    def delete(self, entry_id: str):
        """
        Delete an entry from the database.
        
        Args:
            entry_id (str): The ID of the entry to delete.
        """
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(points=[entry_id])
        )

    def get_current_standards(self) -> List[str]:
        """
        Retrieve the current ethical standards from the database.
        
        Returns:
            List[str]: A list of current ethical standards.
        """
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="type",
                        match=models.MatchValue(value="ethical_standard")
                    )
                ]
            ),
            limit=100  # Adjust as needed
        )[0]

        return [result.payload["content"] for result in results if "content" in result.payload]

    def add_ethical_standard(self, standard: str, embedding: List[float]):
        """
        Add a new ethical standard to the database.
        
        Args:
            standard (str): The ethical standard to add.
            embedding (List[float]): The vector embedding of the standard.
        """
        self.add(embedding, standard, {"type": "ethical_standard"})

    def update_ethical_standard(self, standard_id: str, new_standard: str, new_embedding: List[float]):
        """
        Update an existing ethical standard in the database.
        
        Args:
            standard_id (str): The ID of the standard to update.
            new_standard (str): The updated ethical standard.
            new_embedding (List[float]): The new vector embedding of the standard.
        """
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=standard_id,
                    vector=new_embedding,
                    payload={"content": new_standard, "type": "ethical_standard"}
                )
            ]
        )

    def delete_ethical_standard(self, standard_id: str):
        """
        Delete an ethical standard from the database.
        
        Args:
            standard_id (str): The ID of the standard to delete.
        """
        self.delete(standard_id)

    def bulk_add(self, embeddings: List[List[float]], contents: List[str], metadata_list: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """
        Add multiple entries to the vector database in bulk.
        
        Args:
            embeddings (List[List[float]]): List of vector embeddings.
            contents (List[str]): List of content strings.
            metadata_list (Optional[List[Dict[str, Any]]]): List of metadata dictionaries.
        
        Returns:
            List[str]: List of IDs of the newly added entries.
        """
        if metadata_list is None:
            metadata_list = [{} for _ in contents]

        entry_ids = [str(uuid.uuid4()) for _ in contents]
        points = [
            models.PointStruct(
                id=entry_id,
                vector=embedding,
                payload={"content": content, **metadata}
            )
            for entry_id, embedding, content, metadata in zip(entry_ids, embeddings, contents, metadata_list)
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        return entry_ids

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database.
        
        Returns:
            Dict[str, Any]: Statistics about the database.
        """
        collection_info = self.client.get_collection(self.collection_name)
        return {
            "vectors_count": collection_info.vectors_count,
            "points_count": collection_info.points_count,
            "segments_count": collection_info.segments_count,
            "config": collection_info.config,
        }