"""Tests for care plan service."""

from __future__ import annotations

import uuid

from backend.service.care_plan_service import CARE_PLAN_DISCLAIMER, CarePlanService


class TestCarePlanService:
    def test_extract_from_synthesis_pending(self) -> None:
        svc = CarePlanService.__new__(CarePlanService)
        care = svc.extract_from_synthesis(
            {
                "care_plan": {
                    "medications": [{"name": "Amoxicillin", "purpose": "infection"}],
                    "recovery": {"foods_to_eat": ["broth"]},
                },
            }
        )
        assert care["status"] == "pending_physician_approval"
        assert care["disclaimer"] == CARE_PLAN_DISCLAIMER
        assert care["medications"][0]["name"] == "Amoxicillin"

    def test_approve_sets_status(self, client) -> None:
        email = f"careplan-{uuid.uuid4().hex[:8]}@medvision.health"
        password = "Password1!"
        client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Care Plan Physician",
                "role": "PHYSICIAN",
            },
        )
        login = client.post("/auth/login", json={"email": email, "password": password})
        token = login.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        upload = client.post(
            "/api/clinical/cases",
            headers=headers,
            data={
                "patient_external_id": f"P-CP-{uuid.uuid4().hex[:6]}",
                "patient_name": "Care Plan Patient",
                "symptom_transcript": '[{"role":"patient","message_text":"fever and cough for 3 days"}]',
            },
        )
        assert upload.status_code == 200
        encounter_id = upload.json()["data"]["encounter_id"]

        detail = client.get(f"/api/clinical/encounters/{encounter_id}", headers=headers)
        summary_id = detail.json()["data"].get("summary", {}).get("id")
        if not summary_id:
            regen = client.post(
                f"/api/clinical/encounters/{encounter_id}/synthesis/regenerate",
                headers=headers,
            )
            assert regen.status_code == 200
            detail = client.get(f"/api/clinical/encounters/{encounter_id}", headers=headers)

        plan_get = client.get(
            f"/api/clinical/encounters/{encounter_id}/care-plan",
            headers=headers,
        )
        assert plan_get.status_code == 200
        assert plan_get.json()["data"]["care_plan"].get("status", "pending_physician_approval")

        approve = client.post(
            f"/api/clinical/encounters/{encounter_id}/care-plan/approve",
            headers=headers,
        )
        assert approve.status_code == 200
        assert approve.json()["data"]["care_plan"]["status"] == "approved"
