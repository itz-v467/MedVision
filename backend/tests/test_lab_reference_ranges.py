"""Lab reference range classification tests."""

from __future__ import annotations

from backend.utils.lab_reference_ranges import classify_biomarker, summarize_abnormal_results


class TestLabReferenceRanges:
    """Tests normal vs abnormal lab classification."""

    def test_low_hemoglobin_is_abnormal(self) -> None:
        """Hemoglobin below range is flagged LOW."""
        result = classify_biomarker("Hemoglobin", 10.5)
        assert result["is_abnormal"] is True
        assert result["flag"] == "LOW"
        assert result["status"] == "abnormal"

    def test_normal_wbc(self) -> None:
        """WBC within range is normal."""
        result = classify_biomarker("WBC", 7.0)
        assert result["is_abnormal"] is False
        assert result["status"] == "normal"
        assert result["flag"] == "NORMAL"

    def test_high_ldl_is_abnormal(self) -> None:
        """LDL above threshold is abnormal."""
        result = classify_biomarker("LDL", 160.0)
        assert result["is_abnormal"] is True
        assert result["flag"] == "HIGH"

    def test_summarize_abnormal_results(self) -> None:
        """Summarize helper counts abnormal vs normal markers."""
        biomarkers = [
            classify_biomarker("Glucose", 95.0) | {"name": "Glucose", "value": 95.0},
            classify_biomarker("Glucose", 180.0) | {"name": "Glucose", "value": 180.0},
        ]
        summary = summarize_abnormal_results(biomarkers)
        assert summary["abnormal_count"] == 1
        assert summary["normal_count"] == 1
