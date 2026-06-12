"""Track AI pipeline step execution with timing and summaries."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Generator


class PipelineTracker:
    """Collects ordered pipeline step results for API responses."""

    def __init__(self) -> None:
        """Initialize empty step list."""
        self.steps: list[dict[str, Any]] = []
        self._started = time.perf_counter()

    @contextmanager
    def run_step(
        self,
        step_id: str,
        label: str,
        detail: str,
    ) -> Generator[dict[str, Any], None, None]:
        """Context manager that records step latency and optional summary."""
        record: dict[str, Any] = {"summary": ""}
        started = time.perf_counter()
        try:
            yield record
            status = record.get("status", "completed")
        except Exception:
            self.steps.append(
                {
                    "id": step_id,
                    "label": label,
                    "detail": detail,
                    "status": "failed",
                    "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                    "summary": record.get("summary") or "Step failed",
                }
            )
            raise

        self.steps.append(
            {
                "id": step_id,
                "label": label,
                "detail": detail,
                "status": status,
                "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                "summary": record.get("summary", ""),
            }
        )

    def as_dict(self) -> dict[str, Any]:
        """Serialize pipeline run metadata."""
        total_ms = round((time.perf_counter() - self._started) * 1000, 1)
        return {
            "steps": self.steps,
            "total_latency_ms": total_ms,
            "completed_count": sum(1 for s in self.steps if s["status"] == "completed"),
            "skipped_count": sum(1 for s in self.steps if s["status"] == "skipped"),
        }


PLAIN_STEP_LABELS: dict[str, tuple[str, str]] = {
    "ocr": ("Reading your document", "Scanning the report for test results and patient details"),
    "nlp": ("Understanding medical terms", "Finding conditions, symptoms, and medicines mentioned"),
    "imaging": ("Checking X-ray images", "Looking for areas that may need attention"),
    "correlation": ("Connecting all findings", "Combining labs, notes, and scans"),
    "rag": ("Checking medical references", "Comparing with standard medical guidance"),
    "summary": ("Writing health summary", "Preparing an easy-to-read summary for your doctor"),
    "alerts": ("Safety checks", "Flagging anything that may need urgent care"),
}


def plain_step_label(step_id: str) -> tuple[str, str]:
    """Return doctor/patient-friendly label and detail for a pipeline step."""
    return PLAIN_STEP_LABELS.get(
        step_id, (step_id.replace("_", " ").title(), "Processing")
    )


def summarize_pipeline_step(step_id: str, result: dict[str, Any], file_type: str) -> str:
    """Build a short plain-language summary for a pipeline step."""
    if step_id == "ocr":
        structured = result.get("structured_data", {})
        biomarkers = len(structured.get("biomarkers", []))
        demo = structured.get("patient_demographics", {}).get("full_name", "")
        if biomarkers:
            base = f"Found {biomarkers} test result(s)"
        else:
            base = "Document read successfully"
        if demo:
            return f"{base} · Name on report: {demo}"
        return base

    if step_id == "nlp":
        entities = result.get("entities", {})
        count = (
            sum(len(v) for v in entities.values() if isinstance(v, list))
            if isinstance(entities, dict)
            else 0
        )
        return f"Identified {count} medical term(s)" if count else "Notes reviewed"

    if step_id == "imaging":
        if result.get("skipped"):
            return "Not needed for this document type"
        findings = result.get("findings") or {}
        detected = sum(
            1 for item in findings.values()
            if isinstance(item, dict) and item.get("detected")
        )
        return f"{detected} area(s) flagged on the image"

    if step_id == "correlation":
        return "All results combined for review"

    if step_id == "rag":
        return "Medical references checked"

    if step_id == "summary":
        return "Summary ready for your doctor to review"

    if step_id == "alerts":
        alerts = result if isinstance(result, list) else result.get("alerts", [])
        count = len(alerts) if isinstance(alerts, list) else 0
        return f"{count} reminder(s) added" if count else "No urgent reminders"

    return "Done"
