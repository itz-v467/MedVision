"""Deterministic disease pattern scoring from clinical factors and objective data."""

from __future__ import annotations

from typing import Any


class DiseasePatternEngine:
    """Score likely conditions using weighted multimodal evidence."""

    def match(self, global_context: dict[str, Any]) -> dict[str, Any]:
        """Return ranked pattern_matches list."""
        factors = global_context.get("clinical_factors") or {}
        demographics = factors.get("demographics") or {}
        symptoms = factors.get("symptoms") or {}
        labs = global_context.get("labs") or {}
        imaging_flags = global_context.get("imaging_flags") or {}
        biomarkers = labs.get("biomarkers") or labs.get("abnormal") or []

        present = set(symptoms.get("present_symptoms") or [])
        fever = symptoms.get("fever") or {}
        cough = symptoms.get("cough") or {}
        duration = symptoms.get("symptom_duration_days")
        age = demographics.get("age_years")
        elderly = demographics.get("elderly", False)

        opacity = imaging_flags.get("opacity", {})
        opacity_flagged = bool(opacity.get("detected"))
        opacity_prob = float(opacity.get("probability", 0))

        wbc_high = self._marker_elevated(biomarkers, ("wbc", "white blood", "leukocyte"))
        bilirubin_high = self._marker_elevated(
            biomarkers, ("bilirubin", "total bilirubin")
        )

        matches: list[dict[str, Any]] = []

        def add(
            condition: str,
            score: float,
            evidence: list[str],
            urgency: str = "moderate",
        ) -> None:
            if score < 0.35:
                return
            matches.append(
                {
                    "condition": condition,
                    "score": round(min(score, 0.99), 3),
                    "evidence_factors": evidence,
                    "urgency": urgency,
                }
            )

        resp_score = 0.25
        resp_evidence: list[str] = []
        if "fever" in present or fever.get("present"):
            resp_score += 0.2
            resp_evidence.append("Fever reported")
            if fever.get("duration_days"):
                resp_evidence.append(f"Fever for {fever['duration_days']} day(s)")
        if "cough" in present or cough.get("present"):
            resp_score += 0.2
            resp_evidence.append("Cough reported")
        if opacity_flagged:
            resp_score += 0.3
            resp_evidence.append(f"Lung opacity on imaging ({opacity_prob:.0%})")
        if wbc_high:
            resp_score += 0.15
            resp_evidence.append("Elevated WBC on labs")
        if duration and duration >= 3:
            resp_evidence.append(f"Symptoms for {duration} day(s)")
        if elderly:
            resp_score += 0.1
            resp_evidence.append("Older adult — higher complication risk")

        if opacity_flagged and ("fever" in present or "cough" in present):
            add(
                "Community-acquired pneumonia",
                resp_score,
                resp_evidence,
                urgency="high" if elderly or resp_score >= 0.75 else "moderate",
            )
        elif opacity_flagged:
            add(
                "Lung opacity / consolidation",
                resp_score,
                resp_evidence,
                urgency="moderate",
            )

        if ("fever" in present or "cough" in present) and not opacity_flagged:
            urti_score = 0.45
            urti_ev = [s for s in resp_evidence if "imaging" not in s.lower()]
            if not wbc_high:
                urti_score += 0.1
                urti_ev.append("No significant inflammatory lab spike")
            add("Viral upper respiratory infection", urti_score, urti_ev, "low")

        if bilirubin_high:
            hep_ev = ["Elevated bilirubin on labs"]
            hep_score = 0.55
            if "fever" in present:
                hep_ev.append("Concurrent fever")
                hep_score += 0.1
            add("Hepatobiliary dysfunction / jaundice workup", hep_score, hep_ev, "moderate")

        if "breathlessness" in present and opacity_flagged:
            add(
                "Lower respiratory compromise",
                0.8,
                resp_evidence + ["Dyspnea with imaging abnormality"],
                "high",
            )

        if age and age < 5 and "fever" in present:
            add(
                "Pediatric febrile illness",
                0.6,
                ["Pediatric patient with fever"] + resp_evidence,
                "moderate",
            )

        matches.sort(key=lambda m: m["score"], reverse=True)
        return {
            "pattern_matches": matches[:6],
            "top_condition": matches[0]["condition"] if matches else None,
            "top_score": matches[0]["score"] if matches else 0.0,
        }

    def _marker_elevated(
        self, biomarkers: list[dict[str, Any]], names: tuple[str, ...]
    ) -> bool:
        for marker in biomarkers:
            label = " ".join(
                str(marker.get(k, "")) for k in ("name", "display_name", "test_name")
            ).lower()
            if not any(n in label for n in names):
                continue
            flag = str(marker.get("flag", "")).upper()
            if flag in {"HIGH", "H", "CRITICAL", "ABNORMAL"}:
                return True
            if marker.get("is_abnormal"):
                return True
        return False
