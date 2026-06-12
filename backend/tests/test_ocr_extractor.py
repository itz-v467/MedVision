"""OCR extraction unit tests."""

from __future__ import annotations

from backend.client.ocr_extractor import (
    extraction_warning_for_text,
    parse_biomarkers,
)


class TestOcrExtractor:
    """Tests lab text parsing helpers."""

    def test_parse_biomarkers_from_lab_panel(self) -> None:
        """Extract common blood panel values from free text."""
        text = (
            "Complete Blood Count\n"
            "Hemoglobin: 12.5 g/dL\n"
            "Glucose 98 mg/dL\n"
            "WBC 7.2 10^3/uL\n"
            "Creatinine 1.0 mg/dL"
        )
        biomarkers = parse_biomarkers(text)
        names = {item["name"] for item in biomarkers}
        assert "Hemoglobin" in names
        assert "Glucose" in names
        assert "WBC" in names
        assert "Creatinine" in names

    def test_extraction_warning_for_empty_pdf(self) -> None:
        """Return guidance when PDF text extraction yields nothing."""
        warning = extraction_warning_for_text("", "application/pdf")
        assert warning is not None
        assert "PDF" in warning

    def test_biomarkers_classified_normal_and_abnormal(self) -> None:
        """Mark out-of-range values as abnormal with reference detail."""
        text = "Hemoglobin 11.0 g/dL\nGlucose 92 mg/dL"
        biomarkers = parse_biomarkers(text)
        by_name = {item["name"]: item for item in biomarkers}
        assert by_name["Hemoglobin"]["is_abnormal"] is True
        assert by_name["Hemoglobin"]["flag"] == "LOW"
        assert by_name["Glucose"]["status"] == "normal"
        assert by_name["Glucose"]["is_abnormal"] is False
        assert "reference_range" in by_name["Glucose"]
