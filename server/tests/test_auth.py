from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_invalid_credentials():
    response = client.post(
        "/api/v1/auth/login/access-token",
        data={"username": "wrong@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"
