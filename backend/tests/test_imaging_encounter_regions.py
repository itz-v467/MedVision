"""Integration tests for imaging regions on encounter detail."""

from __future__ import annotations

import io
import uuid

import numpy as np
from PIL import Image


class TestImagingEncounterRegions:
    """Upload chest X-ray and assert non-empty imaging.regions in encounter JSON."""

    def _auth_headers(self, client) -> dict[str, str]:
        email = f"rad-{uuid.uuid4().hex[:8]}@medvision.health"
        password = "Password1!"
        register = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Test Radiologist",
                "role": "RADIOLOGIST",
            },
        )
        assert register.status_code == 201
        login = client.post("/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200
        token = login.json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def _synthetic_xray_png(self) -> io.BytesIO:
        width, height = 512, 512
        arr = np.full((height, width), 70, dtype=np.uint8)
        arr[300:410, 120:250] = 175
        buffer = io.BytesIO()
        Image.fromarray(arr).save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    def test_xray_upload_returns_regions(self, client) -> None:
        """Encounter detail includes normalized anomaly regions after X-ray upload."""
        headers = self._auth_headers(client)
        upload = client.post(
            "/api/clinical/upload",
            headers=headers,
            data={
                "patient_external_id": "P-XRAY-REG",
                "patient_name": "Xray Region Patient",
                "file_type": "xray",
            },
            files={"file": ("chest.png", self._synthetic_xray_png(), "image/png")},
        )
        assert upload.status_code == 200
        encounter_id = upload.json()["data"]["encounter_id"]

        detail = client.get(f"/api/clinical/encounters/{encounter_id}", headers=headers)
        assert detail.status_code == 200
        imaging = detail.json()["data"]["imaging"]
        assert imaging is not None
        regions = imaging.get("regions") or []
        assert len(regions) >= 1
        assert regions[0].get("width", 0) > 0
        assert regions[0].get("height", 0) > 0
        assert imaging.get("imaging_status") in {"ready", "no_regions"}
