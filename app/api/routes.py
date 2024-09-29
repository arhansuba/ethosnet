from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.core.ethosnet import EthosNet
from app.core.llm import LLM
from app.core.vector_db import VectorDB
from app.core.smart_contract import SmartContract

app = FastAPI()

# Dependency to get EthosNet instance
def get_ethosnet():
    return EthosNet()

# Pydantic models for request/response validation
class KnowledgeEntry(BaseModel):
    content: str
    metadata: Optional[dict] = None

class EthicsCheckRequest(BaseModel):
    decision: str

class EthicsScenario(BaseModel):
    scenario: str
    user_decision: str

class ProposalRequest(BaseModel):
    description: str

class VoteRequest(BaseModel):
    proposal_id: str
    support: bool

class ReputationUpdate(BaseModel):
    user: str
    amount: int

@app.post("/knowledge", response_model=dict)
async def add_knowledge(entry: KnowledgeEntry, ethosnet: EthosNet = Depends(get_ethosnet)):
    """Add a new entry to the knowledge base."""
    try:
        result = ethosnet.add_knowledge(entry.content, entry.metadata)
        return {"status": "success", "id": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/knowledge/{entry_id}", response_model=dict)
async def get_knowledge(entry_id: str, ethosnet: EthosNet = Depends(get_ethosnet)):
    """Retrieve a specific knowledge entry."""
    entry = ethosnet.vector_db.get(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@app.put("/knowledge/{entry_id}", response_model=dict)
async def update_knowledge(entry_id: str, entry: KnowledgeEntry, ethosnet: EthosNet = Depends(get_ethosnet)):
    """Update an existing knowledge entry."""
    try:
        ethosnet.vector_db.update(entry_id, entry.content, entry.metadata)
        return {"status": "success", "message": "Entry updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/knowledge/{entry_id}", response_model=dict)
async def delete_knowledge(entry_id: str, ethosnet: EthosNet = Depends(get_ethosnet)):
    """Delete a knowledge entry."""
    try:
        ethosnet.vector_db.delete(entry_id)
        return {"status": "success", "message": "Entry deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/ethics/check", response_model=dict)
async def check_ethics(request: EthicsCheckRequest, ethosnet: EthosNet = Depends(get_ethosnet)):
    """Check the ethics of an AI decision."""
    try:
        result = ethosnet.check_ethics(request.decision)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/ethics/scenario", response_model=dict)
async def submit_ethics_scenario(scenario: EthicsScenario, ethosnet: EthosNet = Depends(get_ethosnet)):
    """Submit and evaluate an ethics scenario."""
    try:
        result = ethosnet.run_ethics_scenario(scenario.scenario, scenario.user_decision)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/governance/propose", response_model=dict)
async def propose_standard(proposal: ProposalRequest, ethosnet: EthosNet = Depends(get_ethosnet)):
    """Propose a new ethical standard."""
    try:
        proposal_id = ethosnet.smart_contract.propose_standard(proposal.description)
        return {"status": "success", "proposal_id": proposal_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/governance/vote", response_model=dict)
async def cast_vote(vote: VoteRequest, ethosnet: EthosNet = Depends(get_ethosnet)):
    """Cast a vote on a proposal."""
    try:
        tx_hash = ethosnet.smart_contract.cast_vote(vote.proposal_id, vote.support)
        return {"status": "success", "transaction_hash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/governance/proposals", response_model=List[dict])
async def get_active_proposals(ethosnet: EthosNet = Depends(get_ethosnet)):
    """Get a list of active proposals."""
    try:
        proposals = ethosnet.smart_contract.get_active_proposals()
        return proposals
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/governance/proposal/{proposal_id}", response_model=dict)
async def get_proposal(proposal_id: str, ethosnet: EthosNet = Depends(get_ethosnet)):
    """Get details of a specific proposal."""
    try:
        proposal = ethosnet.smart_contract.get_proposal(proposal_id)
        return proposal
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/reputation/update", response_model=dict)
async def update_reputation(update: ReputationUpdate, ethosnet: EthosNet = Depends(get_ethosnet)):
    """Update a user's reputation."""
    try:
        tx_hash = ethosnet.smart_contract.update_reputation(update.user, update.amount)
        return {"status": "success", "transaction_hash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/reputation/{user}", response_model=dict)
async def get_reputation(user: str, ethosnet: EthosNet = Depends(get_ethosnet)):
    """Get a user's current reputation."""
    try:
        reputation = ethosnet.smart_contract.get_reputation(user)
        return {"user": user, "reputation": reputation}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/knowledge/search", response_model=List[dict])
async def search_knowledge(query: str, limit: int = 5, ethosnet: EthosNet = Depends(get_ethosnet)):
    """Search the knowledge base for relevant entries."""
    try:
        embedding = ethosnet.llm.embed(query)
        results = ethosnet.vector_db.search(embedding, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/knowledge/summarize", response_model=dict)
async def summarize_topic(topic: str, ethosnet: EthosNet = Depends(get_ethosnet)):
    """Generate a summary on a given ethics topic."""
    try:
        summary = ethosnet.generate_summary(topic)
        return {"topic": topic, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))