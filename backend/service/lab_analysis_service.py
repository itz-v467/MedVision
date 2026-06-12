"""Comprehensive blood panel analysis with standard ranges and precautions."""

from __future__ import annotations

from typing import Any

from backend.utils.lab_catalog import CORE_PANEL, LAB_CATALOG
from backend.utils.lab_reference_ranges import enrich_biomarkers


class LabAnalysisService:
    """Rule-based clinical lab interpreter (standard ranges, not ML-trained)."""

    def analyze_text(self, raw_text: str, *, use_llm: bool = True) -> dict[str, Any]:
        """Parse OCR text, optionally augment with OpenAI, return full panel analysis."""
        from backend.client.lab_llm_extractor import (
            extract_biomarkers_with_llm,
            merge_biomarker_lists,
        )
        from backend.client.ocr_extractor import parse_biomarkers

        regex_biomarkers = parse_biomarkers(raw_text)
        llm_meta: dict[str, Any] = {"used": False, "added_tests": []}

        if use_llm and raw_text.strip():
            llm_biomarkers, llm_meta = extract_biomarkers_with_llm(raw_text)
            biomarkers, added = merge_biomarker_lists(regex_biomarkers, llm_biomarkers)
            llm_meta["added_tests"] = added
            llm_meta["added_count"] = len(added)
        else:
            biomarkers = regex_biomarkers

        analysis = self.analyze_biomarkers(biomarkers)
        analysis["llm_extraction"] = llm_meta
        if llm_meta.get("added_tests"):
            analysis["clinical_summary"] = (
                f"{analysis['clinical_summary']} "
                f"OpenAI extraction added: {', '.join(llm_meta['added_tests'])}."
            )
        return analysis

    def analyze_biomarkers(self, biomarkers: list[dict[str, Any]]) -> dict[str, Any]:
        """Build structured analysis with precautions and coverage."""
        enriched: list[dict[str, Any]] = []
        raw_batch: list[dict[str, Any]] = []
        for item in biomarkers:
            if item.get("status"):
                enriched.append(dict(item))
            else:
                raw_batch.append(item)
        if raw_batch:
            enriched.extend(enrich_biomarkers(raw_batch))
        enriched.sort(key=lambda row: row.get("name", ""))

        abnormal = [b for b in enriched if b.get("is_abnormal")]
        normal = [b for b in enriched if b.get("status") == "normal"]
        detected_names = {b["name"] for b in enriched}
        missing_core = [name for name in CORE_PANEL if name not in detected_names]

        precautions = [
            {
                "test": b["name"],
                "flag": b.get("flag"),
                "value": b.get("display_value"),
                "reference_range": b.get("reference_range"),
                "precaution": b.get("precaution"),
                "severity": "high" if b.get("flag") in {"HIGH", "LOW"} else "moderate",
            }
            for b in abnormal
        ]

        wellness = [
            {
                "test": b["name"],
                "value": b.get("display_value"),
                "message": f"{b['name']} is within standard range. Continue routine health habits.",
            }
            for b in normal
        ]

        coverage = (
            round(len(detected_names & set(CORE_PANEL)) / len(CORE_PANEL) * 100, 1)
            if CORE_PANEL
            else 0.0
        )

        summary_text = self._build_summary(enriched, abnormal, normal, missing_core, coverage)

        return {
            "biomarkers": enriched,
            "abnormal_count": len(abnormal),
            "normal_count": len(normal),
            "total_parsed": len(enriched),
            "panel_coverage_pct": coverage,
            "missing_core_tests": missing_core,
            "precautions": precautions,
            "wellness_notes": wellness,
            "clinical_summary": summary_text,
            "disclaimer": (
                "AI-assisted interpretation using standard adult reference ranges. "
                "Not a diagnosis. Physician review required."
            ),
        }

    def _build_summary(
        self,
        all_markers: list[dict[str, Any]],
        abnormal: list[dict[str, Any]],
        normal: list[dict[str, Any]],
        missing: list[str],
        coverage: float,
    ) -> str:
        """Generate physician-review summary paragraph."""
        parts = [
            f"Blood panel analysis: {len(all_markers)} parameters parsed "
            f"({coverage:.0f}% of core CBC/metabolic panel detected)."
        ]
        if normal:
            parts.append(
                f"Normal ({len(normal)}): {', '.join(b['name'] for b in normal[:8])}"
                + ("…" if len(normal) > 8 else "")
                + "."
            )
        if abnormal:
            parts.append("Abnormal findings requiring attention:")
            for b in abnormal[:6]:
                parts.append(
                    f"• {b['name']} {b.get('display_value')} ({b.get('flag')}) — "
                    f"{b.get('precaution', '')[:120]}"
                )
        if missing:
            parts.append(
                f"Not detected in report (may be absent or OCR missed): "
                f"{', '.join(missing[:6])}."
            )
        parts.append("Correlate with symptoms and local lab reference ranges. Physician review required.")
        return " ".join(parts)
