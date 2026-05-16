from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["provider"] == "azure"
    assert body["index"] == "test-index"


def test_ingest_indexes_chunks(client: TestClient) -> None:
    payload = {
        "text": "\n\n".join(f"Parágrafo {i} sobre renda fixa." * 3 for i in range(6)),
        "source": "test.md",
    }
    response = client.post("/ingest", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["source"] == "test.md"
    assert body["indexed"] >= 1


def test_ingest_rejects_empty_text(client: TestClient) -> None:
    response = client.post("/ingest", json={"text": "", "source": "x.md"})
    assert response.status_code == 422


def test_query_returns_answer_and_sources(client: TestClient) -> None:
    response = client.post(
        "/query",
        json={"question": "O que é Tesouro Selic?", "top_k": 2},
    )
    assert response.status_code == 200
    body = response.json()
    assert "Tesouro Selic" in body["answer"]
    assert len(body["sources"]) == 2
    source = body["sources"][0]
    assert {"chunk", "source", "position", "score"} <= set(source.keys())


def test_query_rejects_short_question(client: TestClient) -> None:
    response = client.post("/query", json={"question": "?"})
    assert response.status_code == 422


def test_openapi_docs_available(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 200
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    paths = schema["paths"]
    assert "/health" in paths
    assert "/ingest" in paths
    assert "/query" in paths
