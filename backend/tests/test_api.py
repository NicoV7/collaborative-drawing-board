import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint returns expected message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Collaborative Drawing Board API"}

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

# Example failing test - implement in TDD cycle
def test_create_drawing_board():
    """Test creating a new drawing board - SHOULD FAIL initially."""
    response = client.post("/boards", json={"name": "Test Board"})
    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["name"] == "Test Board"

# Example failing test - implement in TDD cycle  
def test_get_drawing_boards():
    """Test getting all drawing boards - SHOULD FAIL initially."""
    response = client.get("/boards")
    assert response.status_code == 200
    assert isinstance(response.json(), list)