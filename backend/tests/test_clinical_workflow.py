"""Clinical workflow API tests."""

from __future__ import annotations

import io
import uuid


class TestClinicalWorkflow:
    """Tests encounter detail and summary finalize endpoints."""

    def _auth_headers(self, client) -> dict[str, str]:
        """Register a physician and return auth headers."""
        email = f"physician-{uuid.uuid4().hex[:8]}@medvision.health"
        password = "Password1!"
        register = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Test Physician",
                "role": "PHYSICIAN",
            },
        )
        assert register.status_code == 201
        login = client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        assert login.status_code == 200
        token = login.json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_encounter_detail_not_found(self, client) -> None:
        """Return 404 for unknown encounter."""
        headers = self._auth_headers(client)
        missing_id = "00000000-0000-0000-0000-000000000099"
        response = client.get(f"/api/clinical/encounters/{missing_id}", headers=headers)
        assert response.status_code == 404

    def test_upload_and_finalize_summary(self, client) -> None:
        """Run upload pipeline and finalize generated summary."""
        headers = self._auth_headers(client)
        note = b"Patient with cough and fever. Hemoglobin 12.1 g/dL. Glucose 105 mg/dL."
        upload = client.post(
            "/api/clinical/upload",
            headers=headers,
            data={
                "patient_external_id": "P-TEST-1",
                "patient_name": "Test Patient",
                "file_type": "clinical_note",
            },
            files={"file": ("note.txt", io.BytesIO(note), "text/plain")},
        )
        assert upload.status_code == 200
        payload = upload.json()["data"]
        encounter_id = payload["encounter_id"]
        summary_id = payload["summary"]["summary_id"]

        detail = client.get(f"/api/clinical/encounters/{encounter_id}", headers=headers)
        assert detail.status_code == 200
        detail_data = detail.json()["data"]
        assert detail_data["summary"]["id"] == summary_id

        finalized = client.post(
            f"/api/clinical/summaries/{summary_id}/finalize",
            headers=headers,
        )
        assert finalized.status_code == 200
        assert finalized.json()["data"]["status"] == "FINALIZED"

    def test_timeline_and_alert_acknowledge(self, client) -> None:
        """Return patient timeline and acknowledge generated alerts."""
        headers = self._auth_headers(client)
        note = b"Patient with pneumonia symptoms and cough."
        upload = client.post(
            "/api/clinical/upload",
            headers=headers,
            data={
                "patient_external_id": "P-TIMELINE-1",
                "patient_name": "Timeline Patient",
                "file_type": "clinical_note",
            },
            files={"file": ("note.txt", io.BytesIO(note), "text/plain")},
        )
        assert upload.status_code == 200
        payload = upload.json()["data"]
        encounter_id = payload["encounter_id"]
        patient_id = payload.get("patient_id")

        detail = client.get(f"/api/clinical/encounters/{encounter_id}", headers=headers)
        assert detail.status_code == 200
        detail_data = detail.json()["data"]
        assert detail_data["timeline"]["encounter_count"] >= 1
        patient_id = patient_id or detail_data["patient"]["id"]

        timeline = client.get(
            f"/api/clinical/patients/{patient_id}/timeline", headers=headers
        )
        assert timeline.status_code == 200
        assert timeline.json()["data"]["encounter_count"] >= 1

        if payload.get("alerts"):
            alert_id = payload["alerts"][0]["id"]
            ack = client.post(
                f"/api/clinical/alerts/{alert_id}/acknowledge",
                headers=headers,
            )
            assert ack.status_code == 200
            assert ack.json()["data"]["is_acknowledged"] is True
