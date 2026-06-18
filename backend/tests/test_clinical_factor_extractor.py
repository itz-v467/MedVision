"""Tests for clinical factor extraction."""

from __future__ import annotations

from backend.service.clinical_factor_extractor_service import ClinicalFactorExtractorService


class TestClinicalFactorExtractor:
    def test_fever_three_days_and_age(self) -> None:
        svc = ClinicalFactorExtractorService()
        factors = svc.extract(
            patient={"age": "45"},
            triage_data={
                "messages": [
                    {"role": "patient", "message_text": "fever 102°F and cough for 3 days"},
                ],
            },
        )
        assert factors["demographics"]["age_years"] == 45
        assert factors["symptoms"]["fever"]["present"] is True
        assert factors["symptoms"]["symptom_duration_days"] == 3
        assert "fever" in factors["symptoms"]["present_symptoms"]

    def test_elderly_modifier(self) -> None:
        svc = ClinicalFactorExtractorService()
        factors = svc.extract(patient={"age": "70"})
        assert factors["demographics"]["elderly"] is True
        assert factors["demographics"]["pediatric"] is False

    def test_missing_fever_temperature(self) -> None:
        svc = ClinicalFactorExtractorService()
        factors = svc.extract(
            triage_data={
                "messages": [
                    {"role": "patient", "message_text": "I have had fever for 2 days"},
                ],
            },
        )
        assert "fever_duration_days" not in factors["missing_factors"] or "fever_temperature" in factors["missing_factors"]
        assert "fever_temperature" in factors["missing_factors"]
