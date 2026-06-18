"""Tests for consult request API."""

from __future__ import annotations

import uuid


class TestConsultRequestApi:
    def _auth_headers(self, client, role: str = "PHYSICIAN") -> dict[str, str]:
        email = f"consult-{uuid.uuid4().hex[:8]}@medvision.health"
        password = "Password1!"
        client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Consult Tester",
                "role": role,
            },
        )
        login = client.post("/auth/login", json={"email": email, "password": password})
        token = login.json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_consult_config(self, client) -> None:
        headers = self._auth_headers(client)
        response = client.get("/api/clinical/consult/config", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "default_urgency" in data

    def test_create_and_queue_consult(self, client) -> None:
        headers = self._auth_headers(client)
        upload = client.post(
            "/api/clinical/cases",
            headers=headers,
            data={
                "patient_external_id": f"P-CQ-{uuid.uuid4().hex[:6]}",
                "patient_name": "Consult Patient",
                "symptom_transcript": '[{"role":"patient","message_text":"persistent cough"}]',
            },
        )
        encounter_id = upload.json()["data"]["encounter_id"]

        create = client.post(
            f"/api/clinical/encounters/{encounter_id}/consult/request",
            headers=headers,
            json={"urgency": "within_24h", "reason": "Worsening cough"},
        )
        assert create.status_code == 200
        assert create.json()["data"]["status"] == "pending"

        queue = client.get("/api/clinical/consult/queue", headers=headers)
        assert queue.status_code == 200
        requests = queue.json()["data"]["requests"]
        assert any(r["encounter_id"] == encounter_id for r in requests)
