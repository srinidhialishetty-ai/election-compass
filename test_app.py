from app import app


def test_home_route():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200


def test_assistant_route():
    client = app.test_client()
    response = client.post("/ask", json={"question": "What is election?"})
    assert response.status_code == 200
