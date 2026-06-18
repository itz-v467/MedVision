"""Triage API integration tests."""

from __future__ import annotations

import json
import uuid


class TestTriageApi:
    def _auth_headers(self, client) -> dict[str, str]:
        email = f"triage-{uuid.uuid4().hex[:8]}@medvision.health"
        password = "Password1!"
        client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Triage Tester",
                "role": "PHYSICIAN",
            },
        )
        login = client.post("/auth/login", json={"email": email, "password": password})
        token = login.json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_converse_intake_returns_assistant_reply(self, client) -> None:
        headers = self._auth_headers(client)
        response = client.post(
            "/api/clinical/triage/converse",
            headers=headers,
            json={
                "message": "fever and cough for 2 days",
                "patient_name": "Test Patient",
                "patient_age": "30",
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["messages"]) >= 2
        assert data["assessment"]["risk_level"] in {"low", "moderate", "high", "emergency"}

    def test_symptom_only_case_upload(self, client) -> None:
        headers = self._auth_headers(client)
        transcript = json.dumps([
            {"role": "assistant", "message_text": "What symptoms do you have?"},
            {"role": "patient", "message_text": "mild sore throat for one day"},
        ])
        response = client.post(
            "/api/clinical/cases",
            headers=headers,
            data={
                "patient_external_id": "P-TRIAGE-1",
                "patient_name": "Symptom Only Patient",
                "symptom_transcript": transcript,
            },
        )
        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["case_type"] == "symptom_triage"
        encounter_id = payload["encounter_id"]

        detail = client.get(
            f"/api/clinical/encounters/{encounter_id}",
            headers=headers,
        )
        assert detail.status_code == 200
        triage = detail.json()["data"].get("triage", {})
        assert triage.get("session") is not None

    def test_triage_roadmap_endpoint(self, client) -> None:
        headers = self._auth_headers(client)
        response = client.get("/api/clinical/triage/roadmap", headers=headers)
        assert response.status_code == 200
        roadmap = response.json()["data"]["roadmap"]
        assert len(roadmap) >= 3
