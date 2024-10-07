from typing import List, Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4
from app.core.config import settings
from app.models.knowledge import KnowledgeEntry, ReviewStatus
from app.services.llm_service import LLMService
from app.services.vector_db_service import VectorDBService
from app.services.reputation_service import ReputationService
from app.services.smart_contract_service import SmartContractService

class KnowledgeService:
    def __init__(
        self,
        llm_service: LLMService,
        vector_db_service: VectorDBService,
        reputation_service: ReputationService,
        smart_contract_service: SmartContractService
    ):
        self.llm_service = llm_service
        self.vector_db_service = vector_db_service
        self.reputation_service = reputation_service
        self.smart_contract_service = smart_contract_service

    async def add_entry(self, content: str, metadata: Dict[str, Any], author_id: str) -> str:
        # Generate an embedding for the content
        embedding = await self.llm_service.get_embedding(content)

        # Create a new knowledge entry
        entry_id = str(uuid4())
        entry = KnowledgeEntry(
            id=entry_id,
            content=content,
            metadata=metadata,
            author_id=author_id,
            embedding=embedding,
            created_at=datetime.now(),
            last_reviewed_at=None,
            review_status=ReviewStatus.PENDING,
            quality_score=0,
            relevance_score=0,
            version=1
        )

        # Store the entry in the vector database
        await self.vector_db_service.add_item(
            collection_name="knowledge_base",
            item=entry.dict()
        )

        # Trigger the review process
        await self._trigger_review(entry_id)

        # Record the contribution on the blockchain
        await self.smart_contract_service.record_knowledge_contribution(
            author_id=author_id,
            entry_id=entry_id,
            timestamp=entry.created_at
        )

        return entry_id

    async def get_entry(self, entry_id: str) -> KnowledgeEntry:
        entry_data = await self.vector_db_service.get_item(
            collection_name="knowledge_base",
            id=entry_id
        )
        return KnowledgeEntry(**entry_data)

    async def update_entry(self, entry_id: str, content: str, metadata: Dict[str, Any], author_id: str) -> bool:
        # Retrieve the existing entry
        existing_entry = await self.get_entry(entry_id)

        # Check if the author is allowed to update the entry
        if existing_entry.author_id != author_id:
            raise PermissionError("Only the original author can update the entry.")

        # Generate a new embedding for the updated content
        new_embedding = await self.llm_service.get_embedding(content)

        # Create an updated entry
        updated_entry = KnowledgeEntry(
            **existing_entry.dict(),
            content=content,
            metadata=metadata,
            embedding=new_embedding,
            last_reviewed_at=None,
            review_status=ReviewStatus.PENDING,
            version=existing_entry.version + 1
        )

        # Store the updated entry in the vector database
        await self.vector_db_service.update_item(
            collection_name="knowledge_base",
            id=entry_id,
            item=updated_entry.dict()
        )

        # Trigger the review process
        await self._trigger_review(entry_id)

        return True

    async def delete_entry(self, entry_id: str, requester_id: str) -> bool:
        # Retrieve the existing entry
        existing_entry = await self.get_entry(entry_id)

        # Check if the requester is allowed to delete the entry
        if existing_entry.author_id != requester_id:
            raise PermissionError("Only the original author can delete the entry.")

        # Remove the entry from the vector database
        await self.vector_db_service.delete_item(
            collection_name="knowledge_base",
            id=entry_id
        )

        # Record the deletion on the blockchain
        await self.smart_contract_service.record_knowledge_deletion(
            author_id=requester_id,
            entry_id=entry_id,
            timestamp=datetime.now()
        )

        return True

    async def search_entries(self, query: str, limit: int = 10) -> List[KnowledgeEntry]:
        # Generate an embedding for the query
        query_embedding = await self.llm_service.get_embedding(query)

        # Search for similar entries in the vector database
        similar_entries = await self.vector_db_service.search_similar(
            collection_name="knowledge_base",
            query_vector=query_embedding,
            limit=limit
        )

        return [KnowledgeEntry(**entry) for entry in similar_entries]

    async def _trigger_review(self, entry_id: str):
        # Retrieve the entry
        entry = await self.get_entry(entry_id)

        # Use LLM to assess the quality and relevance of the entry
        assessment = await self._assess_entry(entry)

        # Update the entry with the assessment results
        entry.quality_score = assessment["quality_score"]
        entry.relevance_score = assessment["relevance_score"]
        entry.review_status = ReviewStatus.REVIEWED if assessment["approved"] else ReviewStatus.REJECTED

        # Store the updated entry
        await self.vector_db_service.update_item(
            collection_name="knowledge_base",
            id=entry_id,
            item=entry.dict()
        )

        # Update author's reputation based on the entry's quality and relevance
        reputation_change = (entry.quality_score + entry.relevance_score) / 2
        await self.reputation_service.update_reputation(
            user_id=entry.author_id,
            change=reputation_change,
            reason=f"Knowledge entry {entry_id} review"
        )

        # If the entry is rejected, notify the author
        if entry.review_status == ReviewStatus.REJECTED:
            await self._notify_author_of_rejection(entry.author_id, entry_id, assessment["feedback"])

    async def _assess_entry(self, entry: KnowledgeEntry) -> Dict[str, Any]:
        prompt = f"""
        Assess the following knowledge entry for the EthosNet system:

        Content: {entry.content}
        Metadata: {entry.metadata}

        Provide an assessment including:
        1. Quality score (0-100): How well-written, accurate, and valuable is the content?
        2. Relevance score (0-100): How relevant is this entry to AI ethics and responsible AI development?
        3. Approval status (true/false): Should this entry be approved for inclusion in the knowledge base?
        4. Feedback: Provide constructive feedback, especially if the entry is not approved.

        Format your response as a JSON object.
        """
        return await self.llm_service.generate_json(prompt)

    async def _notify_author_of_rejection(self, author_id: str, entry_id: str, feedback: str):
        # In a real system, this would send a notification to the author
        # For now, we'll just print the information
        print(f"Notification to author {author_id}: Your knowledge entry {entry_id} was rejected.")
        print(f"Feedback: {feedback}")

    async def periodic_reevaluation(self):
        # Get all entries that haven't been reviewed in the last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        entries_to_review = await self.vector_db_service.search(
            collection_name="knowledge_base",
            query_filter={"last_reviewed_at": {"$lt": thirty_days_ago}}
        )

        for entry in entries_to_review:
            await self._trigger_review(entry["id"])

    async def get_community_reviewed_entries(self, limit: int = 10) -> List[KnowledgeEntry]:
        # Get entries that have been approved and have high quality and relevance scores
        high_quality_entries = await self.vector_db_service.search(
            collection_name="knowledge_base",
            query_filter={
                "review_status": ReviewStatus.REVIEWED,
                "quality_score": {"$gt": 80},
                "relevance_score": {"$gt": 80}
            },
            limit=limit
        )

        return [KnowledgeEntry(**entry) for entry in high_quality_entries]

    async def submit_community_review(self, entry_id: str, reviewer_id: str, review_score: int, review_comment: str) -> bool:
        # Retrieve the entry
        entry = await self.get_entry(entry_id)

        # Check if the reviewer has sufficient reputation to submit a review
        reviewer_reputation = await self.reputation_service.get_reputation(reviewer_id)
        if reviewer_reputation < settings.MIN_REPUTATION_FOR_REVIEW:
            raise PermissionError("Insufficient reputation to submit a review.")

        # Record the community review
        review_id = str(uuid4())
        await self.vector_db_service.add_item(
            collection_name="community_reviews",
            item={
                "id": review_id,
                "entry_id": entry_id,
                "reviewer_id": reviewer_id,
                "review_score": review_score,
                "review_comment": review_comment,
                "timestamp": datetime.now()
            }
        )

        # Update the entry's overall scores
        all_reviews = await self.vector_db_service.search(
            collection_name="community_reviews",
            query_filter={"entry_id": entry_id}
        )
        avg_score = sum(review["review_score"] for review in all_reviews) / len(all_reviews)
        entry.quality_score = (entry.quality_score + avg_score) / 2
        
        # Update the entry in the vector database
        await self.vector_db_service.update_item(
            collection_name="knowledge_base",
            id=entry_id,
            item=entry.dict()
        )

        # Update reviewer's reputation
        await self.reputation_service.update_reputation(
            user_id=reviewer_id,
            change=settings.REPUTATION_CHANGE_FOR_REVIEW,
            reason=f"Submitted review for entry {entry_id}"
        )

        return True

    async def generate_knowledge_summary(self, topic: str) -> str:
        # Search for relevant entries
        relevant_entries = await self.search_entries(topic, limit=5)
        
        # Combine the content of relevant entries
        combined_content = "\n\n".join([entry.content for entry in relevant_entries])
        
        # Use LLM to generate a summary
        prompt = f"""
        Given the following information about {topic}:

        {combined_content}

        Generate a concise summary that captures the key points and insights.
        The summary should be informative and relevant to AI ethics and responsible AI development.
        """
        
        summary = await self.llm_service.generate_text(prompt)
        return summary