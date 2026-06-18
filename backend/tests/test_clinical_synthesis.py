"""Tests for global context and clinical synthesis."""

from __future__ import annotations

from backend.client.clinical_synthesis_client import ClinicalSynthesisClient
from backend.service.global_encounter_context_service import GlobalEncounterContextService


class TestGlobalEncounterContext:
    def test_builds_unified_context(self) -> None:
        ctx = GlobalEncounterContextService().build(
            fused={
                "case_type": "multimodal",
                "biomarkers": [{"name": "WBC", "flag": "HIGH", "is_abnormal": True}],
                "document_manifest": [{"file_type": "xray"}],
                "merged_text": "Patient reports cough and fever",
            },
            nlp_result={"entities": {"diseases": ["pneumonia"]}},
            imaging_result={
                "findings": {"opacity": {"probability": 0.72, "detected": True}},
            },
            correlation={"cards": [{"label": "Infection pattern"}]},
            triage_data={
                "session": {"risk_level": "moderate"},
                "messages": [
                    {"role": "patient", "message_text": "cough and fever for 3 days"},
                ],
            },
            patient={"full_name": "Test Patient"},
        )
        assert ctx["symptoms"]["chief_complaint"]
        assert ctx["imaging_flags"]["opacity"]["detected"] is True
        assert len(ctx["labs"]["abnormal"]) == 1
        assert ctx.get("clinical_factors", {}).get("symptoms", {}).get("symptom_duration_days") == 3
        assert ctx.get("pattern_matches", {}).get("pattern_matches")


class TestClinicalSynthesisRules:
    def test_rule_based_respiratory_pattern(self) -> None:
        ClinicalSynthesisClient.reset_instance()
        ctx = {
            "case_type": "multimodal",
            "symptoms": {"chief_complaint": "cough and fever for 3 days", "risk_level": "moderate"},
            "labs": {"abnormal": []},
            "imaging_flags": {"opacity": {"detected": True}},
            "correlation": {
                "cards": [
                    {
                        "label": "Symptom–imaging alignment",
                        "value": "Respiratory symptoms with lung opacity",
                    }
                ]
            },
        }
        result = ClinicalSynthesisClient().synthesize(ctx)
        assert result["engine"] in {"rules", "gemini", "openai"}
        assert result["patient_summary"]
        assert result["physician_summary"]
        assert result.get("leading_diagnosis", {}).get("condition")
        assert "possible_diseases_report" in result
        assert "care_plan" in result
        assert "consult_recommendation" in result
        assert "clinical_factors_review" in result
