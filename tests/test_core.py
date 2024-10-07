import pytest
from app.core.config import settings
from app.core.ethosnet import EthosNet
from app.models.ethics import EthicsEvaluation
from app.models.knowledge import KnowledgeEntry

@pytest.fixture
def ethosnet():
    return EthosNet()

def test_settings():
    assert settings.PROJECT_NAME == "EthosNet"
    assert settings.API_V1_STR == "/api/v1"
    assert isinstance(settings.BACKEND_CORS_ORIGINS, list)

def test_ethics_evaluation(ethosnet):
    decision = "Implement an AI-powered hiring system"
    evaluation = ethosnet.evaluate_ethics(decision)
    assert isinstance(evaluation, EthicsEvaluation)
    assert 0 <= evaluation.decision_score <= 100
    assert evaluation.explanation
    assert isinstance(evaluation.concerns, list)
    assert isinstance(evaluation.improvement_suggestions, list)

def test_knowledge_entry(ethosnet):
    entry = KnowledgeEntry(
        title="Test Entry",
        content="This is a test entry.",
        tags=["test", "core"],
        author_id="user_456"
    )
    added_entry = ethosnet.add_knowledge_entry(entry)
    assert isinstance(added_entry, KnowledgeEntry)
    assert added_entry.id
    assert added_entry.title == entry.title
    assert added_entry.content == entry.content
    assert added_entry.tags == entry.tags
    assert added_entry.author_id == entry.author_id
    assert added_entry.created_at

def test_search_knowledge(ethosnet):
    results = ethosnet.search_knowledge("test")
    assert isinstance(results, list)
    assert all(isinstance(entry, KnowledgeEntry) for entry in results)

