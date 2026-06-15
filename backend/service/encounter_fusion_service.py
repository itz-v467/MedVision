"""Merge per-document AI outputs into one encounter-level clinical context."""

from __future__ import annotations

from typing import Any

from backend.utils.imaging_summary import format_imaging_summary, imaging_attention_items


class EncounterFusionService:
    """Build a unified structured payload from multiple documents."""

    def fuse(
        self,
        *,
        document_results: list[dict[str, Any]],
        imaging_result: dict[str, Any] | None,
        case_type: str,
    ) -> dict[str, Any]:
        """Return fused encounter context for NLP, correlation, and summary."""
        manifest = []
        biomarkers: list[dict[str, Any]] = []
        lab_analysis: dict[str, Any] = {}
        merged_text_parts: list[str] = []
        name_validation = None
        primary_file_type = case_type

        for item in document_results:
            doc = item["document"]
            ocr = item["ocr"]
            structured = ocr.get("structured_data", {}) or {}
            manifest.append(
                {
                    "document_id": str(doc.id),
                    "file_name": doc.file_name,
                    "file_type": doc.file_type,
                    "mime_type": doc.mime_type,
                    "ocr_confidence": ocr.get("confidence", 0),
                    "biomarker_count": len(structured.get("biomarkers", [])),
                }
            )
            text = ocr.get("raw_text") or structured.get("raw_text_preview") or ""
            if text.strip():
                merged_text_parts.append(text.strip())

            if doc.file_type == "lab_report" or doc.file_type == "clinical_note":
                if structured.get("biomarkers"):
                    biomarkers.extend(structured["biomarkers"])
                if structured.get("lab_analysis") and not lab_analysis:
                    lab_analysis = dict(structured["lab_analysis"])

            if structured.get("name_validation") and not name_validation:
                name_validation = structured["name_validation"]

        merged_text = "\n\n".join(merged_text_parts)
        file_types = {m["file_type"] for m in manifest}

        if case_type == "multimodal":
            primary_file_type = "multimodal"
        elif file_types:
            primary_file_type = next(iter(file_types)) if len(file_types) == 1 else "multimodal"

        imaging = imaging_result or {"skipped": True, "findings": {}, "confidence": 0}
        if imaging and not imaging.get("skipped") and case_type in {"multimodal", "single_xray", "xray"}:
            imaging_summary = format_imaging_summary(imaging)
            if not lab_analysis:
                lab_analysis = {
                    "precautions": [],
                    "wellness_notes": [],
                    "panel_coverage_pct": 0.0,
                    "clinical_summary": imaging_summary,
                    "abnormal_count": 0,
                    "normal_count": 0,
                }
            lab_analysis["clinical_summary"] = self._build_multimodal_headline(
                lab_analysis, imaging, case_type
            )
            lab_analysis["precautions"] = [
                {
                    "test": item["test"],
                    "flag": item["flag"],
                    "value": "",
                    "reference_range": "",
                    "precaution": item["text"],
                    "severity": "high" if item["flag"] == "IMAGE" else "moderate",
                }
                for item in imaging_attention_items(imaging)
            ] + list(lab_analysis.get("precautions") or [])

        fused_structured = {
            "document_manifest": manifest,
            "case_type": case_type,
            "biomarkers": biomarkers,
            "lab_analysis": lab_analysis,
            "merged_text_preview": merged_text[:4000],
            "name_validation": name_validation or {},
            "imaging_summary": format_imaging_summary(imaging) if not imaging.get("skipped") else "",
        }

        return {
            "file_type": primary_file_type,
            "case_type": case_type,
            "document_manifest": manifest,
            "merged_text": merged_text,
            "structured_data": fused_structured,
            "biomarkers": biomarkers,
            "lab_analysis": lab_analysis,
            "name_validation": name_validation or {},
            "imaging": imaging,
            "ocr_confidence": max((item["ocr"].get("confidence", 0) for item in document_results), default=0),
        }

    def _build_multimodal_headline(
        self,
        lab_analysis: dict[str, Any],
        imaging: dict[str, Any],
        case_type: str,
    ) -> str:
        """Compose a unified headline when lab and imaging are both present."""
        parts: list[str] = []
        lab_headline = (lab_analysis.get("clinical_summary") or "").split(".")[0]
        imaging_headline = format_imaging_summary(imaging).split(".")[0]

        if case_type == "multimodal":
            if lab_headline and "Blood panel" not in lab_headline:
                parts.append(lab_headline)
            if imaging_headline and imaging_headline not in parts:
                parts.append(imaging_headline)
            if parts:
                return " · ".join(parts) + " — unified case review required"
            return "Multimodal case: review lab and imaging findings together"

        if imaging_headline:
            return imaging_headline
        return lab_headline or "Clinical case ready for physician review"
