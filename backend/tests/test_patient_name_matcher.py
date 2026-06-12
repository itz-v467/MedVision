"""Patient name extraction and matching tests."""

from __future__ import annotations

from backend.utils.patient_demographics_extractor import extract_patient_demographics
from backend.utils.patient_name_matcher import compare_patient_names


class TestPatientNameMatching:
    """OCR name extraction and entered-name validation."""

    def test_extract_name_from_lab_header(self) -> None:
        text = "Patient Name : RAVI PATEL\nAge : 54 Years\nHemoglobin 13.6 g/dL"
        demo = extract_patient_demographics(text)
        assert demo["full_name"] == "Ravi Patel"

    def test_names_match_exact(self) -> None:
        result = compare_patient_names("Ravi Patel", "RAVI PATEL")
        assert result["matched"] is True

    def test_names_mismatch_warns_but_does_not_block(self) -> None:
        result = compare_patient_names("Ravi Patel", "Suresh Kumar")
        assert result["matched"] is False
        assert result.get("blocks_upload") is False
        assert result.get("warning_only") is True

    def test_placeholder_name_rejected(self) -> None:
        result = compare_patient_names("Unknown Patient", "Ravi Patel")
        assert result["matched"] is False

    def test_missing_extracted_name_skips_strict_match(self) -> None:
        result = compare_patient_names("Ravi Patel", "")
        assert result["matched"] is True
        assert result["skipped"] is True
