from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_tasks_unauthorized():
    response = client.get("/api/v1/tasks")
    assert response.status_code == 401
