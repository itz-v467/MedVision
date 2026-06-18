"""Assemble a unified clinical context from all encounter inputs."""

from __future__ import annotations

from typing import Any

from backend.service.clinical_factor_extractor_service import (
    ClinicalFactorExtractorService,
)
from backend.service.disease_pattern_engine import DiseasePatternEngine


class GlobalEncounterContextService:
    """Merge symptoms, labs, imaging, NLP, and correlation into one case view."""

    def __init__(self) -> None:
        self._factor_extractor = ClinicalFactorExtractorService()
        self._pattern_engine = DiseasePatternEngine()

    def build(
        self,
        *,
        fused: dict[str, Any],
        nlp_result: dict[str, Any] | None = None,
        imaging_result: dict[str, Any] | None = None,
        correlation: dict[str, Any] | None = None,
        triage_data: dict[str, Any] | None = None,
        patient: dict[str, Any] | None = None,
        encounter: dict[str, Any] | None = None,
        pattern_matches: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return a doctor-style global case context dict."""
        triage_data = triage_data or {}
        session = triage_data.get("session") or {}
        messages = triage_data.get("messages") or []
        patient_lines = [
            (msg.get("message_text") or msg.get("content") or "").strip()
            for msg in messages
            if (msg.get("role") or "").lower() in {"patient", "user"}
        ]
        symptom_text = " ".join(line for line in patient_lines if line)

        biomarkers = fused.get("biomarkers") or []
        abnormal_labs = [
            b
            for b in biomarkers
            if b.get("is_abnormal")
            or str(b.get("flag", "")).upper() not in {"", "NORMAL", "N"}
        ]

        imaging = imaging_result or fused.get("imaging") or {}
        findings = imaging.get("findings") or {}
        flagged_imaging = {
            name: data
            for name, data in findings.items()
            if isinstance(data, dict) and data.get("detected")
        }

        clinical_factors = self._factor_extractor.extract(
            patient=patient,
            triage_data=triage_data,
            merged_text=fused.get("merged_text") or "",
            chief_complaint=(encounter or {}).get("chief_complaint") or symptom_text[:500],
        )

        base_context: dict[str, Any] = {
            "case_type": fused.get("case_type") or (encounter or {}).get("case_type"),
            "patient": patient or {},
            "encounter": encounter or {},
            "documents": fused.get("document_manifest") or [],
            "clinical_factors": clinical_factors,
            "symptoms": {
                "transcript": messages,
                "chief_complaint": symptom_text[:800] or (encounter or {}).get("chief_complaint"),
                "risk_level": session.get("risk_level"),
                "recommended_disposition": session.get("recommended_disposition"),
                "assessment": session.get("assessment") or {},
            },
            "labs": {
                "biomarkers": biomarkers,
                "abnormal": abnormal_labs,
                "lab_analysis": fused.get("lab_analysis") or {},
            },
            "imaging": imaging,
            "imaging_flags": flagged_imaging,
            "nlp": nlp_result or {},
            "correlation": correlation or {},
            "merged_clinical_text": fused.get("merged_text") or "",
        }

        if pattern_matches is None:
            pattern_matches = self._pattern_engine.match(base_context)
        base_context["pattern_matches"] = pattern_matches
        base_context["reasoning_inputs"] = {
            "clinical_factors": clinical_factors,
            "pattern_matches": pattern_matches,
            "reports_reviewed": [
                doc.get("file_type") or doc.get("file_name")
                for doc in (fused.get("document_manifest") or [])
            ],
        }
        return base_context
