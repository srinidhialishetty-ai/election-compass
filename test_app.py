import app as app_module

app = app_module.app


def test_home_route():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200


def test_assistant_route(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(app_module, "model", None)

    client = app.test_client()
    response = client.post("/ask", json={"question": "What is election?"})
    assert response.status_code == 200
