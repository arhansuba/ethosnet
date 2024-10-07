from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime
from enum import Enum

class ReviewStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    REJECTED = "rejected"
    FLAGGED = "flagged"

class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    CODE = "code"
    DATASET = "dataset"

class KnowledgeEntry(BaseModel):
    id: str
    title: str
    content: str
    content_type: ContentType
    metadata: Dict[str, Any]
    author_id: str
    created_at: datetime
    updated_at: datetime
    last_reviewed_at: datetime = None
    review_status: ReviewStatus
    quality_score: float = Field(..., ge=0, le=100)
    relevance_score: float = Field(..., ge=0, le=100)
    version: int
    tags: List[str]
    references: List[str]
    embedding: List[float] = None

    class Config:
        schema_extra = {
            "example": {
                "id": "ke_001",
                "title": "Introduction to AI Ethics",
                "content": "AI ethics is a system of moral principles and techniques intended to inform the development and responsible use of artificial intelligence technology...",
                "content_type": ContentType.TEXT,
                "metadata": {
                    "source": "AI Ethics Handbook, 2023 Edition",
                    "word_count": 150,
                    "reading_time": "2 minutes"
                },
                "author_id": "user_789",
                "created_at": "2023-05-10T09:00:00Z",
                "updated_at": "2023-05-10T09:00:00Z",
                "last_reviewed_at": "2023-05-11T14:30:00Z",
                "review_status": ReviewStatus.REVIEWED,
                "quality_score": 92.5,
                "relevance_score": 95.0,
                "version": 1,
                "tags": ["AI ethics", "introduction", "principles"],
                "references": ["https://example.com/ai-ethics-handbook"],
                "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]  # This would typically be a much longer list
            }
        }

class KnowledgeEntryCreate(BaseModel):
    title: str
    content: str
    content_type: ContentType
    metadata: Dict[str, Any] = {}
    tags: List[str] = []
    references: List[str] = []

class KnowledgeEntryUpdate(BaseModel):
    title: str = None
    content: str = None
    metadata: Dict[str, Any] = None
    tags: List[str] = None
    references: List[str] = None

class KnowledgeEntryReview(BaseModel):
    reviewer_id: str
    quality_score: float = Field(..., ge=0, le=100)
    relevance_score: float = Field(..., ge=0, le=100)
    review_comments: str
    review_status: ReviewStatus

class KnowledgeSearchResult(BaseModel):
    entry: KnowledgeEntry
    similarity_score: float = Field(..., ge=0, le=1)

class KnowledgeSummary(BaseModel):
    topic: str
    summary: str
    key_points: List[str]
    related_entries: List[str]
    generated_at: datetime