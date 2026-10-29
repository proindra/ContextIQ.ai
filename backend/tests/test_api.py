from fastapi.testclient import TestClient
from langchain_core.documents import Document

from main import create_app


class FakeRAGSystem:
    def run(self, question: str) -> dict:
        return {
            "question": question,
            "answer": "Agents can use tools to complete tasks.",
            "retrieved_docs": [
                Document(
                    page_content="An agent can select a tool based on the task.",
                    metadata={"title": "Agent guide", "source": "https://example.com/agents"},
                )
            ],
        }


def test_health_endpoint() -> None:
    with TestClient(create_app(FakeRAGSystem())) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_search_returns_answer_and_sources() -> None:
    with TestClient(create_app(FakeRAGSystem())) as client:
        response = client.post("/api/search", json={"question": "What can agents do?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["question"] == "What can agents do?"
    assert payload["answer"] == "Agents can use tools to complete tasks."
    assert payload["sources"][0]["title"] == "Agent guide"
    assert payload["sources"][0]["source"] == "https://example.com/agents"
    assert payload["sources"][0]["content"].startswith("An agent can")
    assert payload["elapsed_seconds"] >= 0


def test_search_rejects_blank_question() -> None:
    with TestClient(create_app(FakeRAGSystem())) as client:
        response = client.post("/api/search", json={"question": "   "})

    assert response.status_code == 422


def test_search_reports_provider_failure() -> None:
    class FailedRAGSystem:
        def run(self, question: str) -> dict:
            raise RuntimeError("provider unavailable")

    with TestClient(create_app(FailedRAGSystem())) as client:
        response = client.post("/api/search", json={"question": "Try again"})

    assert response.status_code == 502
    assert "Search failed" in response.json()["detail"]
