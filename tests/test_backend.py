from __future__ import annotations

from backend.app.main import app
from backend.app.routers import ask as ask_router
from backend.app.routers import evidence as evidence_router
from backend.app.routers import health as health_router
from backend.app.routers import layers as layers_router
from backend.app.schemas.ask import AskRequest
from backend.app.schemas.evidence import EvidenceSearchRequest
from backend.app.services import orchestrator_service


def test_health() -> None:
    payload = health_router.health()
    assert payload["status"] == "ok"
    assert "readiness" in payload
    assert "supabase_service_role_configured" in payload["readiness"]["configuration"]
    assert "SUPABASE_SERVICE_ROLE_KEY" not in str(payload)


def test_layers() -> None:
    response = layers_router.layers()
    layers = {item.layer: item for item in response.layers}
    assert layers["diabetes"].active is True
    assert layers["diabetes_ckd"].active is False
    assert layers["diabetes_cvd"].active is False
    assert layers["diabetes_pregnancy"].active is False
    assert layers["diabetes_hypertension"].active is False


def test_ask_refuses_insulin_dosing() -> None:
    response = ask_router.ask_question(
        AskRequest(
            question="How much insulin should I take after rice?",
            disease_layer="diabetes",
            language="en",
            top_k=5,
            show_chunks=True,
        )
    )
    assert response.safety["safety_label"] == "refuse"
    assert "refused" in str(response.answer)
    assert response.retrieval.chunks == []
    assert response.citation_validation
    assert response.substitutions == []


def test_ask_refuses_inactive_ckd_layer() -> None:
    response = ask_router.ask_question(
        AskRequest(
            question="I have diabetes and kidney disease. Can I eat bananas daily?",
            disease_layer="diabetes",
            language="en",
            top_k=5,
            show_chunks=True,
        )
    )
    assert response.safety["safety_label"] == "refuse"
    assert "kidney" in response.safety["reason"].lower() or "inactive" in response.safety["reason"].lower()
    assert response.retrieval.chunks == []


def test_ask_refuses_unrelated_out_of_scope() -> None:
    response = ask_router.ask_question(
        AskRequest(
            question="Who won the world cup?",
            disease_layer="diabetes",
            language="en",
            top_k=5,
            show_chunks=True,
        )
    )
    assert response.safety["safety_label"] == "refuse"
    assert "outside" in response.safety["reason"].lower()
    assert response.retrieval.chunks == []


def test_ask_response_shape_with_mocked_pipeline(monkeypatch) -> None:
    def fake_pipeline(question: str, disease_layer: str = "diabetes", top_k: int = 5) -> dict:
        del disease_layer, top_k
        return {
            "query": question,
            "layer": {"effective_layer": "diabetes", "can_answer": True},
            "safety_result": {"safety_label": "allowed", "reason": "ok", "recommended_action": "answer_with_evidence"},
            "chunks": [
                {
                    "chunk_id": "chk-demo",
                    "document_title": "ADA Standards of Care 2026",
                    "section_title": "Nutrition",
                    "page_start": 5,
                    "page_end": 5,
                    "citation_label": "ADA 2026 p.5",
                    "chunk_type": "recommendation",
                    "disease_layer": "diabetes",
                    "similarity": 0.91,
                    "content": "Legumes provide fiber and plant protein for diabetes nutrition patterns.",
                }
            ],
            "confidence": {"top_similarity": 0.91, "threshold": 0.55, "status": "sufficient", "can_answer": True},
            "answer": "Food Safety Classification:\nencouraged\n\nCitations:\nchunk ID chk-demo\n\nSafety Note:\nThis is not a personalized diet plan.",
            "citation_validation": {"valid": True, "failures": [], "cited_chunk_ids": ["chk-demo"]},
            "substitutions": [],
            "unsupported_claims": [],
        }

    monkeypatch.setattr(orchestrator_service, "run_full_pipeline", fake_pipeline)
    response = ask_router.ask_question(AskRequest(question="Are legumes encouraged for diabetes?", show_chunks=True))
    payload = response.model_dump()
    assert set(["answer", "retrieval", "citation_validation"]).issubset(payload)
    assert "chunks" in payload["retrieval"]
    assert payload["retrieval"]["chunks"][0]["chunk_id"] == "chk-demo"
    assert payload["citation_validation"]["valid"] is True


def test_evidence_search_returns_chunks_key(monkeypatch) -> None:
    def fake_retrieve_evidence(
        query: str,
        disease_layer: str = "diabetes",
        top_k: int = 5,
        clinical_topic: str = "diabetes_food_safety",
    ) -> dict:
        del top_k, clinical_topic
        return {
            "confidence": "sufficient",
            "top_score": 0.88,
            "chunks": [
                {
                    "chunk_id": "chk-evidence",
                    "document_title": "ADA Standards of Care 2026",
                    "section_title": "Nutrition",
                    "page_start": 5,
                    "page_end": 5,
                    "citation_label": "ADA 2026 p.5",
                    "chunk_type": "recommendation",
                    "disease_layer": disease_layer,
                    "similarity": 0.88,
                    "content": f"Evidence for {query}",
                }
            ],
        }

    monkeypatch.setattr(evidence_router, "retrieve_evidence", fake_retrieve_evidence)
    response = evidence_router.search_evidence(
        EvidenceSearchRequest(
            query="Are legumes encouraged for diabetes?",
            disease_layer="diabetes",
            top_k=3,
        )
    )
    payload = response.model_dump()
    assert payload["query"] == "Are legumes encouraged for diabetes?"
    assert payload["disease_layer"] == "diabetes"
    assert "chunks" in payload
    assert payload["chunks"][0]["chunk_id"] == "chk-evidence"


def test_openapi_schema_contains_answer_chunks_and_citations() -> None:
    schema_text = str(app.openapi())
    assert "answer" in schema_text
    assert "chunks" in schema_text
    assert "citation_validation" in schema_text or "citations" in schema_text
