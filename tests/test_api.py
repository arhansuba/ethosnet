import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to EthosNet API"}

def test_evaluate_ethics():
    decision = "Implement facial recognition in public spaces"
    response = client.post(f"{settings.API_V1_STR}/ethics/evaluate", json={"decision": decision})
    assert response.status_code == 200
    data = response.json()
    assert "decision_score" in data
    assert "explanation" in data
    assert "concerns" in data
    assert "improvement_suggestions" in data

def test_get_ethical_guidelines():
    response = client.get(f"{settings.API_V1_STR}/ethics/guidelines")
    assert response.status_code == 200
    guidelines = response.json()
    assert isinstance(guidelines, list)
    assert len(guidelines) > 0

def test_add_knowledge_entry():
    entry = {
        "title": "Test Entry",
        "content": "This is a test entry for the knowledge base.",
        "tags": ["test", "api"],
        "author_id": "user_123"
    }
    response = client.post(f"{settings.API_V1_STR}/knowledge/add", json=entry)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == entry["title"]
    assert data["content"] == entry["content"]
    assert data["tags"] == entry["tags"]
    assert data["author_id"] == entry["author_id"]

def test_search_knowledge():
    query = "ethics"
    response = client.get(f"{settings.API_V1_STR}/knowledge/search?query={query}")
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    for entry in results:
        assert "id" in entry
        assert "title" in entry
        assert "content" in entry
        assert "tags" in entry
        assert "author_id" in entry
        assert "created_at" in entry

