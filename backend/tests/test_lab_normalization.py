"""Lab value normalization tests."""

from __future__ import annotations

from backend.client.ocr_extractor import parse_biomarkers
from backend.utils.lab_value_normalizer import normalize_biomarker
from backend.utils.lab_reference_ranges import classify_biomarker


class TestLabNormalization:
    """Ensure counts and units normalize to standard clinical scales."""

    def test_platelets_absolute_count_to_standard_scale(self) -> None:
        """226000/cumm should normalize to 226 10^3/uL and be normal."""
        norm = normalize_biomarker("Platelets", 226000, "")
        assert norm["value"] == 226.0
        result = classify_biomarker("Platelets", norm["value"])
        assert result["status"] == "normal"
        assert result["is_abnormal"] is False

    def test_wbc_absolute_count(self) -> None:
        """7200 WBC should become 7.2 10^3/uL."""
        norm = normalize_biomarker("WBC", 7200, "")
        assert norm["value"] == 7.2
        assert classify_biomarker("WBC", norm["value"])["status"] == "normal"

    def test_parse_indian_comma_format(self) -> None:
        """Parse platelet count with Indian comma grouping."""
        text = "Platelets 2,26,000 /cumm\nHemoglobin 13.6 g/dL\nUrea 19.4 mg/dL"
        biomarkers = parse_biomarkers(text)
        by_name = {b["name"]: b for b in biomarkers}
        assert by_name["Platelets"]["status"] == "normal"
        assert by_name["Platelets"]["value"] == 226.0
        assert by_name["Hemoglobin"]["status"] == "normal"
