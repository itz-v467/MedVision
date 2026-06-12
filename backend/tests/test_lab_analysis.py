"""Comprehensive blood panel analysis tests."""

from __future__ import annotations

from backend.client.ocr_extractor import parse_biomarkers
from backend.service.lab_analysis_service import LabAnalysisService
from backend.utils.lab_reference_ranges import classify_biomarker, get_precaution


class TestLabAnalysis:
    """Standard-range classification and precautions."""

    def test_low_hemoglobin_precaution(self) -> None:
        result = classify_biomarker("Hemoglobin", 9.5)
        assert result["status"] == "abnormal"
        assert result["flag"] == "LOW"
        assert "anemia" in result["precaution"].lower()

    def test_normal_glucose_precaution(self) -> None:
        result = classify_biomarker("Glucose", 92.0)
        assert result["status"] == "normal"
        assert "within standard range" in get_precaution("Glucose", "NORMAL", False).lower()

    def test_full_panel_analysis(self) -> None:
        text = """
        Hemoglobin 13.6 g/dL
        RBC 4.8 10^6/uL
        WBC 7.2 10^3/uL
        Platelets 2,26,000 /cumm
        Hematocrit 42 %
        Glucose 118 mg/dL
        Urea 19.4 mg/dL
        Creatinine 0.9 mg/dL
        LDL 145 mg/dL
        HDL 38 mg/dL
        """
        analysis = LabAnalysisService().analyze_text(text)
        assert analysis["total_parsed"] >= 8
        assert analysis["panel_coverage_pct"] >= 75.0
        glucose = next(b for b in analysis["biomarkers"] if b["name"] == "Glucose")
        assert glucose["is_abnormal"] is True
        assert any(p["test"] == "Glucose" for p in analysis["precautions"])
        platelets = next(b for b in analysis["biomarkers"] if b["name"] == "Platelets")
        assert platelets["status"] == "normal"

    def test_parse_biomarkers_include_precaution(self) -> None:
        biomarkers = parse_biomarkers("ALT 78 U/L\nHemoglobin 14 g/dL")
        by_name = {b["name"]: b for b in biomarkers}
        assert by_name["ALT"]["is_abnormal"] is True
        assert by_name["ALT"].get("precaution")
        assert by_name["Hemoglobin"]["status"] == "normal"
