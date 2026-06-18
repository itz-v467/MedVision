"""Rule-based symptom risk scoring and emergency escalation."""

from __future__ import annotations

import re
from typing import Any

from backend.constants.triage_policy import (
    DISPOSITION_BY_RISK,
    EMERGENCY_RED_FLAG_PATTERNS,
    RISK_LEVELS,
)


class TriageRiskScoringService:
    """Score symptom text for urgency and red-flag escalation."""

    def score(self, text: str, *, patient_age: str | None = None) -> dict[str, Any]:
        """Return risk level, disposition, matched flags, and rationale bullets."""
        normalized = (text or "").lower()
        matched_flags: list[dict[str, str]] = []

        for flag_id, patterns in EMERGENCY_RED_FLAG_PATTERNS:
            for pattern in patterns:
                if pattern in normalized:
                    matched_flags.append({"id": flag_id, "pattern": pattern})
                    break

        if matched_flags:
            return self._build_assessment(
                risk_level="emergency",
                matched_flags=matched_flags,
                rationale=[
                    "Emergency red-flag symptoms detected in patient report.",
                    "Immediate emergency medical evaluation is recommended.",
                ],
            )

        high_signals = [
            "severe pain",
            "high fever",
            "fever above 103",
            "blood in stool",
            "blood in urine",
            "worst headache",
            "sudden vision loss",
        ]
        moderate_signals = [
            "fever",
            "cough",
            "vomiting",
            "diarrhea",
            "fatigue",
            "dizziness",
            "pain",
        ]

        high_hits = [s for s in high_signals if s in normalized]
        moderate_hits = [s for s in moderate_signals if s in normalized]

        if high_hits:
            return self._build_assessment(
                risk_level="high",
                matched_flags=[],
                rationale=[
                    f"High-urgency symptom language detected: {', '.join(high_hits[:3])}.",
                    "Same-day medical evaluation is advisable.",
                ],
            )

        if len(moderate_hits) >= 2:
            return self._build_assessment(
                risk_level="moderate",
                matched_flags=[],
                rationale=[
                    f"Multiple symptom indicators: {', '.join(moderate_hits[:4])}.",
                    "Clinic follow-up within 24–48 hours is reasonable if symptoms persist.",
                ],
            )

        if moderate_hits:
            return self._build_assessment(
                risk_level="moderate",
                matched_flags=[],
                rationale=[
                    f"Symptom reported: {moderate_hits[0]}.",
                    "Monitor closely and seek care if worsening.",
                ],
            )

        age_note = ""
        if patient_age and patient_age.isdigit() and int(patient_age) >= 65:
            age_note = "Older adult — lower threshold for in-person evaluation if symptoms worsen."

        rationale = ["No emergency red flags detected in current message."]
        if age_note:
            rationale.append(age_note)

        return self._build_assessment(
            risk_level="low",
            matched_flags=[],
            rationale=rationale,
        )

    def score_conversation(self, messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        """Score full transcript; highest risk wins."""
        assessments = [
            self.score(msg.get("message_text") or msg.get("content") or "", **kwargs)
            for msg in messages
            if (msg.get("role") or "").lower() in {"user", "patient"}
        ]
        if not assessments:
            return self.score("", **kwargs)

        order = {level: idx for idx, level in enumerate(RISK_LEVELS)}
        return max(assessments, key=lambda a: order.get(a["risk_level"], 0))

    def extract_symptom_keywords(self, text: str) -> list[str]:
        """Lightweight symptom token extraction for structured storage."""
        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9\-]{2,}", (text or "").lower())
        symptom_vocab = {
            "fever", "cough", "pain", "headache", "nausea", "vomiting", "diarrhea",
            "fatigue", "dizziness", "rash", "breathlessness", "chest", "throat",
            "weakness", "numbness", "swelling", "bleeding",
        }
        return sorted({t for t in tokens if t in symptom_vocab})

    def _build_assessment(
        self,
        *,
        risk_level: str,
        matched_flags: list[dict[str, str]],
        rationale: list[str],
    ) -> dict[str, Any]:
        return {
            "risk_level": risk_level,
            "recommended_disposition": DISPOSITION_BY_RISK.get(risk_level, ""),
            "emergency_flags": matched_flags,
            "rationale": rationale,
            "escalation_required": risk_level in {"high", "emergency"},
        }
