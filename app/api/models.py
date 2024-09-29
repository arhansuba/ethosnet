from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MetadataType(str, Enum):
    STANDARD = "standard"
    SCENARIO = "scenario"
    DECISION = "decision"
    CONTRIBUTION = "contribution"

class KnowledgeEntryBase(BaseModel):
    content: str = Field(..., description="The main content of the knowledge entry")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata for the entry")

class KnowledgeEntryCreate(KnowledgeEntryBase):
    metadata_type: MetadataType = Field(..., description="The type of metadata for this entry")

class KnowledgeEntry(KnowledgeEntryBase):
    id: str = Field(..., description="Unique identifier for the knowledge entry")
    created_at: datetime = Field(..., description="Timestamp of when the entry was created")
    updated_at: datetime = Field(..., description="Timestamp of when the entry was last updated")

class KnowledgeEntryUpdate(BaseModel):
    content: Optional[str] = Field(None, description="Updated content of the knowledge entry")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata for the entry")

class EthicsCheckRequest(BaseModel):
    decision: str = Field(..., description="The AI decision to be evaluated for ethical compliance")

class EthicsCheckResponse(BaseModel):
    decision: str = Field(..., description="The original AI decision")
    evaluation: str = Field(..., description="Ethical evaluation of the decision")
    compliant: bool = Field(..., description="Whether the decision is ethically compliant")
    score: float = Field(..., ge=0, le=1, description="Ethical compliance score (0-1)")

class EthicsScenario(BaseModel):
    scenario: str = Field(..., description="Description of the ethical scenario")
    user_decision: str = Field(..., description="The user's decision in response to the scenario")

class EthicsScenarioResponse(BaseModel):
    scenario: str = Field(..., description="The original ethical scenario")
    user_decision: str = Field(..., description="The user's decision")
    feedback: str = Field(..., description="Feedback on the ethical implications of the decision")
    learning_points: List[str] = Field(..., description="Key learning points from this scenario")

class ProposalStatus(str, Enum):
    ACTIVE = "active"
    PASSED = "passed"
    REJECTED = "rejected"
    EXECUTED = "executed"

class ProposalCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=100, description="Title of the proposal")
    description: str = Field(..., min_length=20, description="Detailed description of the proposal")
    url: Optional[HttpUrl] = Field(None, description="URL with additional information about the proposal")

class Proposal(ProposalCreate):
    id: str = Field(..., description="Unique identifier for the proposal")
    proposer: str = Field(..., description="Ethereum address of the proposer")
    status: ProposalStatus = Field(..., description="Current status of the proposal")
    start_block: int = Field(..., description="Block number when voting starts")
    end_block: int = Field(..., description="Block number when voting ends")
    for_votes: int = Field(..., ge=0, description="Number of votes in favor")
    against_votes: int = Field(..., ge=0, description="Number of votes against")

class VoteRequest(BaseModel):
    proposal_id: str = Field(..., description="ID of the proposal to vote on")
    support: bool = Field(..., description="True to vote in favor, False to vote against")

class VoteResponse(BaseModel):
    proposal_id: str = Field(..., description="ID of the proposal voted on")
    user: str = Field(..., description="Ethereum address of the voter")
    support: bool = Field(..., description="Whether the vote was in favor")
    weight: int = Field(..., ge=0, description="Weight of the vote (based on reputation)")
    transaction_hash: str = Field(..., description="Transaction hash of the vote")

class ReputationUpdate(BaseModel):
    user: str = Field(..., description="Ethereum address of the user")
    amount: int = Field(..., description="Amount to update the reputation by (positive or negative)")
    reason: str = Field(..., description="Reason for the reputation update")

class ReputationResponse(BaseModel):
    user: str = Field(..., description="Ethereum address of the user")
    reputation: int = Field(..., ge=0, description="Current reputation score of the user")
    last_updated: datetime = Field(..., description="Timestamp of the last reputation update")

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Search query")
    limit: int = Field(5, ge=1, le=100, description="Maximum number of results to return")

class SearchResult(BaseModel):
    id: str = Field(..., description="ID of the knowledge entry")
    content: str = Field(..., description="Content of the knowledge entry")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata of the knowledge entry")
    score: float = Field(..., ge=0, le=1, description="Relevance score of the search result")

class SummaryRequest(BaseModel):
    topic: str = Field(..., min_length=3, description="Topic to summarize")

class SummaryResponse(BaseModel):
    topic: str = Field(..., description="Original topic")
    summary: str = Field(..., description="Generated summary")

class UserContribution(BaseModel):
    user: str = Field(..., description="Ethereum address of the contributor")
    contribution_type: str = Field(..., description="Type of contribution (e.g., 'knowledge', 'proposal', 'vote')")
    content: str = Field(..., description="Content of the contribution")
    timestamp: datetime = Field(..., description="Timestamp of the contribution")
    impact_score: Optional[float] = Field(None, ge=0, le=1, description="Impact score of the contribution")

class UserProfile(BaseModel):
    address: str = Field(..., description="Ethereum address of the user")
    reputation: int = Field(..., ge=0, description="Current reputation score")
    contribution_count: int = Field(..., ge=0, description="Total number of contributions")
    joined_at: datetime = Field(..., description="Timestamp when the user joined")
    last_active: datetime = Field(..., description="Timestamp of the user's last activity")
    areas_of_expertise: List[str] = Field(default=[], description="User's areas of expertise")