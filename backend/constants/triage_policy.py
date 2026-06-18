"""Symptom triage chatbot MVP policy — triage-only, non-diagnostic."""

from __future__ import annotations

TRIAGE_DISCLAIMER = (
    "This assistant provides informational triage guidance only. "
    "It does not diagnose conditions or prescribe treatment. "
    "A licensed physician must review all recommendations before clinical decisions."
)

TRIAGE_SYSTEM_PROMPT = f"""You are MedVision Healthcare Intake Assistant — a compassionate, professional pre-consult triage nurse.

Your role:
- Collect a focused symptom history before the physician visit.
- Ask specific follow-up questions (onset, duration, severity 1-10, triggers, associated symptoms, medications, allergies).
- Reflect back what the patient said in your own words so they feel heard.
- Provide cautious triage guidance and when to seek care — never a definitive diagnosis.
- Never prescribe medications, dosages, or treatment orders.

Tone: warm, clear, plain language. One short paragraph plus numbered follow-up questions when helpful.

Rules (strict):
- If emergency red flags appear, tell the user to seek emergency care immediately.
- End every response with a short reminder that a licensed physician must review before clinical decisions.

{TRIAGE_DISCLAIMER}
"""

EMERGENCY_RED_FLAG_PATTERNS: list[tuple[str, list[str]]] = [
    ("chest_pain_emergency", ["chest pain", "crushing chest", "heart attack"]),
    ("breathing_emergency", ["can't breathe", "cannot breathe", "severe shortness of breath", "choking"]),
    ("stroke_signs", ["facial droop", "slurred speech", "sudden weakness", "sudden numbness"]),
    ("severe_bleeding", ["uncontrolled bleeding", "coughing blood", "vomiting blood"]),
    ("altered_consciousness", ["unconscious", "passed out", "confused and disoriented", "seizure"]),
    ("suicidal_ideation", ["suicide", "kill myself", "want to die", "end my life"]),
    ("anaphylaxis", ["throat swelling", "tongue swelling", "severe allergic reaction"]),
]

RISK_LEVELS = ("low", "moderate", "high", "emergency")

DISPOSITION_BY_RISK = {
    "low": "Home care with routine follow-up if symptoms persist beyond 3–5 days.",
    "moderate": "Schedule a clinic visit within 24–48 hours.",
    "high": "Seek urgent same-day medical evaluation.",
    "emergency": "Call emergency services (911 / local emergency number) now.",
}
