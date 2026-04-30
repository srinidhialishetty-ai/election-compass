import app as app_module

app = app_module.app


def test_home_route():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200


def test_assistant_page_route():
    client = app.test_client()
    response = client.get("/assistant")
    assert response.status_code == 200


def test_assistant_api_uses_fallback_without_gemini_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(app_module, "model", None)

    client = app.test_client()
    response = client.post("/ask", json={"question": "What is election?"})
    assert response.status_code == 200
    assert response.get_json()["used_fallback"] is True


def test_assistant_api_can_use_mocked_gemini(monkeypatch):
    class FakeModel:
        def generate_content(self, prompt):
            class FakeResponse:
                text = (
                    '{"heading":"Election Overview","answer":"Elections begin with preparation. '
                    'Voters then participate through the official voting process. Results are counted and confirmed.",'
                    '"bullets":[],"clarification":"","example":"","topic":"overview",'
                    '"recommended_section":"assistant","suggestions":["Show me the election timeline",'
                    '"Explain voting day","What happens after voting?","Give me a quick recap"]}'
                )

            return FakeResponse()

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(app_module, "model", FakeModel())

    client = app.test_client()
    response = client.post(
        "/api/assistant",
        json={"question": "What is election?", "style": "simple"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["source"] == "gemini"
    assert data["used_fallback"] is False
    assert len([part for part in data["answer"].split(".") if part.strip()]) <= 3
