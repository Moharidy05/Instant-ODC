from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "readiness" in payload
    assert "supabase_service_role_configured" in payload["readiness"]["configuration"]
    assert "SUPABASE_SERVICE_ROLE_KEY" not in str(payload)


def test_layers() -> None:
    response = client.get("/layers")
    assert response.status_code == 200
    layers = {item["layer"]: item for item in response.json()["layers"]}
    assert layers["diabetes"]["active"] is True
    assert layers["diabetes_ckd"]["active"] is False
    assert layers["diabetes_cvd"]["active"] is False
    assert layers["diabetes_pregnancy"]["active"] is False
    assert layers["diabetes_hypertension"]["active"] is False


def test_ask_refuses_insulin_dosing() -> None:
    response = client.post(
        "/ask",
        json={
            "question": "How much insulin should I take after rice?",
            "disease_layer": "diabetes",
            "language": "en",
            "top_k": 5,
            "show_chunks": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["safety"]["safety_label"] == "refuse"
    assert "refused" in payload["answer"]
    assert payload["retrieval"]["chunks"] == []
    assert "citation_validation" in payload
    assert "substitutions" in payload


def test_evidence_search_returns_chunks_key() -> None:
    response = client.post(
        "/evidence/search",
        json={
            "query": "Are legumes encouraged for diabetes?",
            "disease_layer": "diabetes",
            "top_k": 3,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "Are legumes encouraged for diabetes?"
    assert payload["disease_layer"] == "diabetes"
    assert "chunks" in payload
