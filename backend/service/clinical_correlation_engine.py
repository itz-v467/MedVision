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
        pneumothorax = findings.get("pneumothorax", {})
        ptx_flagged = bool(pneumothorax.get("detected"))

        triage = fused.get("triage") or {}
        triage_session = triage.get("session") or {}
        triage_messages = triage.get("messages") or []
        symptom_text = " ".join(
            (msg.get("message_text") or msg.get("content") or "").strip()
            for msg in triage_messages
            if (msg.get("role") or "").lower() in {"patient", "user"}
        ).lower()
        triage_risk = triage_session.get("risk_level") or ""
        has_cough_fever = "cough" in symptom_text and "fever" in symptom_text
        has_breath_symptoms = any(
            term in symptom_text
            for term in ("shortness of breath", "breathless", "dyspnea", "can't breathe")
        )
        has_chest_pain = "chest pain" in symptom_text or "chest discomfort" in symptom_text

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

        if (has_cough_fever or "pneumonia" in symptom_text) and opacity_flagged:
            cards.append({
                "label": "Symptom–imaging alignment",
                "value": "Respiratory symptoms with lung opacity on X-ray",
                "note": "Pattern consistent with lower respiratory infection — correlate with exam and vitals.",
                "tone": "alert",
            })
            correlations.append({
                "type": "symptom_imaging_respiratory",
                "description": "Cough/fever symptoms with radiographic opacity",
                "weight": 0.88,
            })

        if has_breath_symptoms and (opacity_flagged or ptx_flagged):
            cards.append({
                "label": "Dyspnea correlation",
                "value": "Breathing difficulty with abnormal chest imaging",
                "note": "Assess oxygen saturation and urgency of respiratory evaluation.",
                "tone": "alert",
            })
            correlations.append({
                "type": "symptom_imaging_dyspnea",
                "description": "Dyspnea with chest imaging abnormality",
                "weight": 0.9,
            })

        if has_chest_pain and (ptx_flagged or opacity_flagged):
            cards.append({
                "label": "Chest symptom + imaging",
                "value": "Chest pain reported with significant X-ray finding",
                "note": "Urgent physician review — exclude serious cardiopulmonary causes.",
                "tone": "alert",
            })
            correlations.append({
                "type": "symptom_imaging_chest_pain",
                "description": "Chest pain with radiographic abnormality",
                "weight": 0.92,
            })

        if triage_risk in {"emergency", "high"} and (opacity_flagged or abnormal_labs):
            cards.append({
                "label": "High-urgency intake",
                "value": f"Symptom triage risk: {triage_risk}",
                "note": "Symptom severity aligns with objective findings — prioritize physician review.",
                "tone": "alert",
            })
            correlations.append({
                "type": "triage_objective_alignment",
                "description": f"Elevated triage risk ({triage_risk}) with objective abnormalities",
                "weight": 0.85,
            })

        nlp_entities = fused.get("nlp_entities") or {}
        if isinstance(nlp_entities, dict):
            diseases = nlp_entities.get("diseases") or []
            if diseases and opacity_flagged:
                cards.append({
                    "label": "NLP–imaging link",
                    "value": f"Clinical entities ({', '.join(diseases[:2])}) with imaging flags",
                    "note": "Text-derived conditions overlap imaging — verify in full chart review.",
                    "tone": "alert",
                })

        clinical_factors = fused.get("clinical_factors") or {}
        pattern_matches = fused.get("pattern_matches") or {}
        demographics = clinical_factors.get("demographics") or {}
        factor_symptoms = clinical_factors.get("symptoms") or {}
        age_years = demographics.get("age_years")
        fever_days = (factor_symptoms.get("fever") or {}).get("duration_days")
        symptom_duration = factor_symptoms.get("symptom_duration_days")

        if age_years is not None and opacity_flagged and has_cough_fever:
            age_note = f"Age {age_years}"
            if fever_days:
                age_note += f", fever {fever_days} day(s)"
            elif symptom_duration:
                age_note += f", symptoms {symptom_duration} day(s)"
            cards.append({
                "label": "Clinical factor pattern",
                "value": f"{age_note} with lung opacity",
                "note": "Multi-factor respiratory infection pattern — physician should confirm with exam and vitals.",
                "tone": "alert",
            })

        top_patterns = pattern_matches.get("pattern_matches") or []
        for match in top_patterns[:2]:
            cards.append({
                "label": "Disease pattern match",
                "value": f"{match.get('condition')} ({match.get('score', 0):.0%})",
                "note": "; ".join(match.get("evidence_factors") or [])[:200],
                "tone": "alert" if match.get("urgency") == "high" else None,
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
            "symptom_context": symptom_text[:500] if symptom_text else None,
            "triage_risk": triage_risk or None,
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
