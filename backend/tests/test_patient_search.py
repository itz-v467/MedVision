"""Patient search API tests."""

import uuid

from backend.db import get_database_manager
from backend.model.patient_model import PatientModel
from backend.service.patient_search_service import PatientSearchService


def _auth_headers(client) -> dict[str, str]:
    email = f"search-{uuid.uuid4().hex[:8]}@medvision.health"
    password = "Password1!"
    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Search Tester",
            "role": "PHYSICIAN",
        },
    )
    login = client.post("/auth/login", json={"email": email, "password": password})
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_patient_text_search(app):
    with get_database_manager().session_scope() as session:
        session.add(
            PatientModel(external_id="MV-20260101-0001", full_name="Ravi Patel", gender="Male")
        )
        session.flush()
        hits = PatientSearchService(session).search("Ravi", limit=5)

    assert len(hits) >= 1
    assert hits[0]["external_id"] == "MV-20260101-0001"


def test_patient_search_ignores_irrelevant_vector_hits(app):
    """Keyword search should not return unrelated patients as AI matches."""
    suffix = uuid.uuid4().hex[:6]
    with get_database_manager().session_scope() as session:
        session.add(
            PatientModel(
                external_id=f"MV-TEST-{suffix}-001",
                full_name="kartik",
                gender="Female",
            )
        )
        session.add(
            PatientModel(
                external_id=f"MV-TEST-{suffix}-002",
                full_name="atharva",
                gender="Male",
            )
        )
        session.add(
            PatientModel(
                external_id=f"MV-TEST-{suffix}-003",
                full_name="raj",
                gender="Male",
            )
        )
        session.flush()
        hits = PatientSearchService(session).search("kartik", limit=10)

    names = {hit["full_name"] for hit in hits}
    assert "kartik" in names
    assert "atharva" not in names
    assert "raj" not in names


def test_patient_search_endpoint(client, app):
    with get_database_manager().session_scope() as session:
        session.add(
            PatientModel(external_id="MV-20260101-0099", full_name="Jane Doe")
        )

    headers = _auth_headers(client)
    response = client.get(
        "/api/clinical/patients/search?q=Jane",
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert any(p["full_name"] == "Jane Doe" for p in body["data"]["patients"])
