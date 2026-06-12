"""OpenAI lab extraction merge tests (no live API calls)."""

from __future__ import annotations

from unittest.mock import patch

from backend.client.lab_llm_extractor import (
    extract_biomarkers_with_llm,
    merge_biomarker_lists,
    resolve_canonical_name,
)
from backend.service.lab_analysis_service import LabAnalysisService
from backend.utils.lab_reference_ranges import enrich_biomarkers


class TestLabLlmExtractor:
    """Merge and canonical name resolution."""

    def test_resolve_canonical_alias(self) -> None:
        assert resolve_canonical_name("sgpt") == "ALT"
        assert resolve_canonical_name("BUN") == "Urea"
        assert resolve_canonical_name("unknown test") is None

    def test_merge_keeps_regex_over_llm(self) -> None:
        regex = enrich_biomarkers([{"name": "Glucose", "value": 95, "unit": "mg/dL"}])
        llm = [{"name": "Glucose", "value": 200, "unit": "mg/dL"}, {"name": "ALT", "value": 78, "unit": "U/L"}]
        merged, added = merge_biomarker_lists(regex, llm)
        by_name = {b["name"]: b for b in merged}
        assert by_name["Glucose"]["value"] == 95.0
        assert by_name["ALT"]["value"] == 78.0
        assert added == ["ALT"]

    @patch("backend.client.lab_llm_extractor.get_openai_client")
    def test_analyze_text_augments_with_llm(self, mock_client_factory) -> None:
        mock_client = mock_client_factory.return_value
        mock_client.extract_structured_json.return_value = {
            "biomarkers": [
                {"name": "MCHC", "value": 33.5, "unit": "g/dL"},
                {"name": "RDW", "value": 13.2, "unit": "%"},
            ]
        }
        with patch("backend.client.lab_llm_extractor.get_settings") as mock_settings:
            settings = mock_settings.return_value
            settings.openai_enabled = True
            settings.openai_lab_extraction_enabled = True
            settings.openai_llm_model = "gpt-4o-mini"

            text = "Hemoglobin 14 g/dL\nGlucose 92 mg/dL"
            analysis = LabAnalysisService().analyze_text(text, use_llm=True)

        names = {b["name"] for b in analysis["biomarkers"]}
        assert "MCHC" in names
        assert "RDW" in names
        assert analysis["llm_extraction"]["added_count"] == 2

    def test_extract_skipped_without_api_key(self) -> None:
        with patch("backend.client.lab_llm_extractor.get_settings") as mock_settings:
            settings = mock_settings.return_value
            settings.openai_enabled = False
            settings.openai_lab_extraction_enabled = True
            biomarkers, meta = extract_biomarkers_with_llm("Hemoglobin 12 g/dL")
        assert biomarkers == []
        assert meta["used"] is False
