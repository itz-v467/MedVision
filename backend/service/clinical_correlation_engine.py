"""Clinical lab↔imaging correlation rules (FR-COR-01)."""

from __future__ import annotations

from typing import Any


class ClinicalCorrelationEngine:
    """Produce physician-facing cross-modal correlation cards."""

    def correlate(self, fused: dict[str, Any]) -> dict[str, Any]:
        """Analyze fused encounter context and return correlation artifacts."""
        biomarkers = fused.get("biomarkers") or []
        imaging = fused.get("imaging") or {}
        findings = imaging.get("findings") or {}
        case_type = fused.get("case_type", "")

        cards: list[dict[str, Any]] = []
        correlations: list[dict[str, Any]] = []

        abnormal_labs = [
            b for b in biomarkers
            if b.get("is_abnormal") or str(b.get("flag", "")).upper() not in {"", "NORMAL", "N"}
        ]
        opacity = findings.get("opacity", {})
        opacity_prob = float(opacity.get("probability", 0))
        opacity_flagged = bool(opacity.get("detected"))

        wbc = self._find_marker(biomarkers, ("wbc", "white blood", "leukocyte"))
        hb = self._find_marker(biomarkers, ("hemoglobin", "haemoglobin", "hb"))
        glucose = self._find_marker(biomarkers, ("glucose", "blood sugar"))
        cardiomegaly = findings.get("cardiomegaly", {})
        cardio_flagged = bool(cardiomegaly.get("detected"))

        if wbc and self._is_elevated(wbc) and opacity_flagged:
            cards.append({
                "label": "Infection pattern",
                "value": "Elevated WBC with lung opacity",
                "note": "Possible lower respiratory infection — correlate with symptoms and exam.",
                "tone": "alert",
            })
            correlations.append({
                "type": "lab_imaging_infection",
                "description": "Elevated WBC with radiographic opacity",
                "weight": 0.85,
            })

        if hb and self._is_low(hb) and not opacity_flagged:
            cards.append({
                "label": "Anemia workup",
                "value": "Low hemoglobin, chest film without major opacity",
                "note": "Anemia is unlikely explained by the chest X-ray — consider GI or hematology review.",
                "tone": "alert",
            })
            correlations.append({
                "type": "lab_imaging_anemia",
                "description": "Anemia without explanatory chest findings",
                "weight": 0.7,
            })

        if not abnormal_labs and opacity_flagged:
            cards.append({
                "label": "Imaging-led finding",
                "value": "Opacity on X-ray without flagged lab inflammatory markers",
                "note": "May represent early infection, atelectasis, or non-infectious opacity — clinical correlation needed.",
                "tone": "alert",
            })
            correlations.append({
                "type": "imaging_only_opacity",
                "description": "Radiographic opacity without abnormal labs",
                "weight": 0.75,
            })

        if glucose and self._is_elevated(glucose) and cardio_flagged:
            cards.append({
                "label": "Cardiometabolic pattern",
                "value": "Elevated glucose with enlarged cardiac silhouette",
                "note": "Review cardiac history, medications, and metabolic risk factors.",
                "tone": "alert",
            })
            correlations.append({
                "type": "metabolic_cardiac",
                "description": "Hyperglycemia with cardiomegaly on imaging",
                "weight": 0.65,
            })

        if case_type == "multimodal" and not cards:
            cards.append({
                "label": "Multimodal case",
                "value": "Lab and imaging reviewed together",
                "note": "No automatic cross-modal flags — physician should synthesize all documents.",
            })

        ocr_score = float(fused.get("ocr_confidence", 0))
        imaging_score = float(imaging.get("confidence", 0))
        nlp_score = float(fused.get("nlp_confidence", 0))

        if case_type == "multimodal":
            weighted = (imaging_score * 0.4) + (ocr_score * 0.4) + (nlp_score * 0.2)
        elif imaging.get("skipped"):
            weighted = (ocr_score * 0.65) + (nlp_score * 0.35)
        else:
            weighted = (imaging_score * 0.5) + (ocr_score * 0.25) + (nlp_score * 0.25)

        return {
            "weighted_evidence_score": round(weighted, 4),
            "correlations": correlations,
            "cards": cards,
            "case_type": case_type,
        }

    def _find_marker(
        self, biomarkers: list[dict[str, Any]], names: tuple[str, ...]
    ) -> dict[str, Any] | None:
        for marker in biomarkers:
            label = " ".join(
                str(marker.get(key, "")) for key in ("name", "display_name", "test_name")
            ).lower()
            if any(name in label for name in names):
                return marker
        return None

    def _is_elevated(self, marker: dict[str, Any]) -> bool:
        flag = str(marker.get("flag", "")).upper()
        if flag in {"HIGH", "H", "CRITICAL", "ABNORMAL"}:
            return True
        status = str(marker.get("status", "")).lower()
        return status in {"high", "abnormal", "critical"}

    def _is_low(self, marker: dict[str, Any]) -> bool:
        flag = str(marker.get("flag", "")).upper()
        if flag in {"LOW", "L", "CRITICAL", "ABNORMAL"}:
            return True
        status = str(marker.get("status", "")).lower()
        return status in {"low", "abnormal", "critical"}
