import pytest
from app.services.ethics_service import EthicsService
from app.services.knowledge_service import KnowledgeService
from app.services.llm_service import LLMService
from app.services.reputation_service import ReputationService
from app.services.smart_contract_service import SmartContractService
from app.services.vector_db_service import VectorDBService

@pytest.fixture
def ethics_service():
    return EthicsService()

@pytest.fixture
def knowledge_service():
    return KnowledgeService()

@pytest.fixture
def llm_service():
    return LLMService()

@pytest.fixture
def reputation_service():
    return ReputationService()

@pytest.fixture
def smart_contract_service():
    return SmartContractService()

@pytest.fixture
def vector_db_service():
    return VectorDBService()

def test_ethics_service(ethics_service):
    decision = "Implement an AI system for credit scoring"
    evaluation = ethics_service.evaluate_ethics(decision)
    assert evaluation.decision_score is not None
    assert evaluation.explanation
    assert evaluation.concerns
    assert evaluation.improvement_suggestions

def test_knowledge_service(knowledge_service):
    entry = {
        "title": "Test Entry",
        "content": "This is a test entry for the knowledge service.",
        "tags": ["test", "service"],
        "author_id": "user_789"
    }
    added_entry = knowledge_service.add_entry(entry)
    assert added_entry.id
    assert added_entry.title == entry["title"]
    
    search_results = knowledge_service.search_entries("test")
    assert len(search_results) > 0
    assert any(e.title == "Test Entry" for e in search_results)

def test_llm_service(llm_service):
    prompt = "Summarize the importance of AI ethics in one sentence."
    response = llm_service.generate_text(prompt)
    assert isinstance(response, str)
    assert len(response) > 0

def test_reputation_service(reputation_service):
    user_id = "user_123"
    initial_reputation = reputation_service.get_reputation(user_id)
    reputation_service.update_reputation(user_id, 5.0, "Positive contribution")
    updated_reputation = reputation_service.get_reputation(user_id)
    assert updated_reputation > initial_reputation

def test_smart_contract_service(smart_contract_service):
    user_id = "user_456"
    new_reputation = 75.5
    tx_hash = smart_contract_service.update_reputation(user_id, new_reputation)
    assert tx_hash
    stored_reputation = smart_contract_service.get_reputation(user_id)
    assert abs(stored_reputation - new_reputation) < 0.01

def test_vector_db_service(vector_db_service):
    vector = [0.1, 0.2, 0.3, 0.4, 0.5]
    payload = {"content": "Test vector entry"}
    vector_db_service.add_item("test_collection", "test_id", vector, payload)
    
    results = vector_db_service.search_similar("test_collection", vector, limit=1)
    assert len(results) == 1
    assert results[0]["id"] == "test_id"

