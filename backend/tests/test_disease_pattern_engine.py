"""Tests for disease pattern engine."""

from __future__ import annotations

from backend.service.disease_pattern_engine import DiseasePatternEngine


class TestDiseasePatternEngine:
    def test_pneumonia_pattern_from_cough_fever_opacity(self) -> None:
        ctx = {
            "clinical_factors": {
                "demographics": {"age_years": 45, "elderly": False},
                "symptoms": {
                    "present_symptoms": ["fever", "cough"],
                    "fever": {"present": True, "duration_days": 3},
                    "cough": {"present": True},
                    "symptom_duration_days": 3,
                },
            },
            "imaging_flags": {
                "opacity": {"detected": True, "probability": 0.66},
            },
            "labs": {"biomarkers": [{"name": "WBC", "flag": "HIGH"}]},
        }
        result = DiseasePatternEngine().match(ctx)
        matches = result["pattern_matches"]
        assert matches
        top = matches[0]
        assert "pneumonia" in top["condition"].lower()
        assert top["score"] >= 0.7

    def test_viral_urti_without_opacity(self) -> None:
        ctx = {
            "clinical_factors": {
                "demographics": {"age_years": 30},
                "symptoms": {
                    "present_symptoms": ["cough", "fever"],
                    "fever": {"present": True},
                    "cough": {"present": True},
                },
            },
            "imaging_flags": {"opacity": {"detected": False}},
            "labs": {"biomarkers": []},
        }
        result = DiseasePatternEngine().match(ctx)
        conditions = [m["condition"].lower() for m in result["pattern_matches"]]
        assert any("urti" in c or "viral" in c for c in conditions)
