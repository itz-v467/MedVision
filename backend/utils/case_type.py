"""Encounter case-type helpers for single vs multimodal uploads."""

from __future__ import annotations

from typing import Iterable


def infer_case_type(file_types: Iterable[str]) -> str:
    """Classify an encounter from its document manifest."""
    types = {ft for ft in file_types if ft}
    if not types:
        return "symptom_triage"
    if len(types) > 1:
        return "multimodal"
    only = next(iter(types))
    if only == "lab_report":
        return "single_lab"
    if only == "xray":
        return "single_xray"
    if only == "symptom_triage":
        return "symptom_triage"
    return "single_note"
