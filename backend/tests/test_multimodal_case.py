"""Tests for unified multi-document clinical case upload."""

from __future__ import annotations

import io
import uuid

import numpy as np
from PIL import Image


class TestMultimodalCase:
    """Lab + X-ray in one encounter via POST /api/clinical/cases."""

    def _auth_headers(self, client) -> dict[str, str]:
        email = f"phys-{uuid.uuid4().hex[:8]}@medvision.health"
        password = "Password1!"
        register = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Case Physician",
                "role": "PHYSICIAN",
            },
        )
        assert register.status_code == 201
        login = client.post("/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200
        return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}

    def _xray_png(self) -> io.BytesIO:
        arr = np.full((256, 256), 80, dtype=np.uint8)
        arr[140:200, 80:150] = 170
        buffer = io.BytesIO()
        Image.fromarray(arr).save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    def test_lab_plus_xray_single_encounter(self, client) -> None:
        """One case creates two documents and multimodal correlation."""
        headers = self._auth_headers(client)
        lab_csv = b"test,value,unit,flag\nWBC,12.5,10^3/uL,HIGH\nHemoglobin,11.2,g/dL,LOW"

        response = client.post(
            "/api/clinical/cases",
            headers=headers,
            data={
                "patient_external_id": "P-MULTI-1",
                "patient_name": "Jane Doe",
                "file_types": ["lab_report", "xray"],
            },
            files=[
                ("files", ("panel.csv", io.BytesIO(lab_csv), "text/csv")),
                ("files", ("chest.png", self._xray_png(), "image/png")),
            ],
        )
        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["case_type"] == "multimodal"
        assert len(payload.get("document_ids", [])) == 2

        encounter_id = payload["encounter_id"]
        detail = client.get(f"/api/clinical/encounters/{encounter_id}", headers=headers)
        assert detail.status_code == 200
        data = detail.json()["data"]
        assert len(data["documents"]) == 2
        assert data["encounter"]["case_type"] == "multimodal"
        assert data.get("correlation", {}).get("cards")
        assert data.get("imaging") is not None
        assert data.get("summary", {}).get("summary_text")
