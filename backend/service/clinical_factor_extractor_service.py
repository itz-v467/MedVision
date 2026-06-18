"""Extract structured clinical factors from multimodal encounter inputs."""

from __future__ import annotations

import re
from typing import Any

_SYMPTOM_KEYWORDS = {
    "fever": ["fever", "temperature", "temp", "chills"],
    "cough": ["cough", "coughing"],
    "headache": ["headache", "migraine"],
    "chest_pain": ["chest pain", "chest tight", "chest pressure"],
    "breathlessness": ["breath", "breathing", "shortness of breath", "sob", "dyspnea"],
    "nausea": ["nausea", "vomit", "vomiting"],
    "rash": ["rash", "hives"],
    "dizziness": ["dizzy", "dizziness", "lightheaded"],
    "throat": ["sore throat", "throat pain"],
    "fatigue": ["fatigue", "tired", "weakness"],
}

_COMORBIDITY_KEYWORDS = [
    "diabetes",
    "asthma",
    "copd",
    "heart disease",
    "hypertension",
    "pregnancy",
    "pregnant",
    "cancer",
    "kidney",
    "liver disease",
    "hiv",
    "immunocompromised",
]

_DURATION_PATTERN = re.compile(
    r"(?:for\s+)?(\d+)\s*(day|days|week|weeks|hour|hours|month|months)",
    re.IGNORECASE,
)
_TEMP_F_PATTERN = re.compile(
    r"(\d{2,3}(?:\.\d+)?)\s*(?:°?\s*f|fahrenheit)",
    re.IGNORECASE,
)
_TEMP_C_PATTERN = re.compile(
    r"(\d{2}(?:\.\d+)?)\s*(?:°?\s*c|celsius)",
    re.IGNORECASE,
)


class ClinicalFactorExtractorService:
    """Parse age, symptom duration, fever, and comorbidities from case data."""

    def extract(
        self,
        *,
        patient: dict[str, Any] | None = None,
        triage_data: dict[str, Any] | None = None,
        merged_text: str = "",
        chief_complaint: str | None = None,
    ) -> dict[str, Any]:
        """Return structured clinical_factors dict."""
        patient = patient or {}
        triage_data = triage_data or {}
        messages = triage_data.get("messages") or []

        patient_lines = [
            (msg.get("message_text") or msg.get("content") or "").strip()
            for msg in messages
            if (msg.get("role") or "").lower() in {"patient", "user"}
        ]
        symptom_text = " ".join(line for line in patient_lines if line)
        if chief_complaint:
            symptom_text = f"{chief_complaint} {symptom_text}".strip()
        if merged_text and merged_text not in symptom_text:
            symptom_text = f"{symptom_text} {merged_text[:500]}".strip()

        age_years = self._parse_age(patient.get("date_of_birth") or patient.get("age"))
        gender = (patient.get("gender") or "").strip().lower() or None

        present_symptoms = self._detect_symptoms(symptom_text)
        duration_days = self._extract_duration_days(symptom_text)
        fever_info = self._extract_fever(symptom_text, present_symptoms)
        comorbidities = self._extract_comorbidities(symptom_text)
        onset = self._detect_onset(symptom_text)
        red_flags = self._extract_red_flags(triage_data)

        completeness = self._score_completeness(
            age_years=age_years,
            symptom_text=symptom_text,
            present_symptoms=present_symptoms,
            duration_days=duration_days,
            fever_info=fever_info,
        )

        return {
            "demographics": {
                "age_years": age_years,
                "gender": gender,
                "elderly": age_years is not None and age_years >= 65,
                "pediatric": age_years is not None and age_years < 18,
            },
            "symptoms": {
                "chief_complaint": symptom_text[:800] or None,
                "present_symptoms": present_symptoms,
                "fever": fever_info,
                "cough": {
                    "present": "cough" in present_symptoms,
                    "productive": self._detect_productive_cough(symptom_text),
                },
                "symptom_duration_days": duration_days,
                "onset": onset,
            },
            "comorbidities_mentioned": comorbidities,
            "red_flags": red_flags,
            "data_completeness": completeness,
            "missing_factors": self._missing_factors(
                age_years, fever_info, duration_days, present_symptoms
            ),
        }

    def _parse_age(self, raw: Any) -> int | None:
        if raw is None:
            return None
        text = str(raw).strip()
        if not text:
            return None
        if text.isdigit():
            value = int(text)
            return value if 0 < value < 130 else None
        match = re.search(r"\b(\d{1,3})\s*(?:years?|yrs?|yo)\b", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def _detect_symptoms(self, text: str) -> list[str]:
        lowered = text.lower()
        found: list[str] = []
        for name, keywords in _SYMPTOM_KEYWORDS.items():
            if any(kw in lowered for kw in keywords):
                found.append(name)
        return found

    def _extract_duration_days(self, text: str) -> int | None:
        best: int | None = None
        for match in _DURATION_PATTERN.finditer(text):
            amount = int(match.group(1))
            unit = match.group(2).lower()
            if unit.startswith("hour"):
                days = max(1, amount // 24)
            elif unit.startswith("week"):
                days = amount * 7
            elif unit.startswith("month"):
                days = amount * 30
            else:
                days = amount
            if best is None or days > best:
                best = days
        return best

    def _extract_fever(
        self, text: str, present_symptoms: list[str]
    ) -> dict[str, Any]:
        has_fever = "fever" in present_symptoms
        max_temp_c: float | None = None

        f_match = _TEMP_F_PATTERN.search(text)
        if f_match:
            f_val = float(f_match.group(1))
            max_temp_c = round((f_val - 32) * 5 / 9, 1)

        c_match = _TEMP_C_PATTERN.search(text)
        if c_match:
            max_temp_c = float(c_match.group(1))

        fever_days = None
        if has_fever:
            fever_context = re.search(
                r"fever.{0,40}?(\d+)\s*(?:day|days)",
                text,
                re.IGNORECASE,
            )
            if fever_context:
                fever_days = int(fever_context.group(1))

        return {
            "present": has_fever,
            "duration_days": fever_days,
            "max_temp_c": max_temp_c,
        }

    def _extract_comorbidities(self, text: str) -> list[str]:
        lowered = text.lower()
        return [c for c in _COMORBIDITY_KEYWORDS if c in lowered]

    def _detect_onset(self, text: str) -> str | None:
        lowered = text.lower()
        if any(w in lowered for w in ("sudden", "suddenly", "acute")):
            return "sudden"
        if any(w in lowered for w in ("gradual", "slowly", "progressive")):
            return "gradual"
        return None

    def _detect_productive_cough(self, text: str) -> bool | None:
        lowered = text.lower()
        if any(w in lowered for w in ("productive", "phlegm", "mucus", "sputum")):
            return True
        if "dry cough" in lowered:
            return False
        return None

    def _extract_red_flags(self, triage_data: dict[str, Any]) -> list[str]:
        session = triage_data.get("session") or {}
        assessment = session.get("assessment") or {}
        flags = assessment.get("emergency_flags") or []
        return [
            f.get("id") or f.get("pattern", "red_flag")
            for f in flags
            if isinstance(f, dict)
        ]

    def _score_completeness(
        self,
        *,
        age_years: int | None,
        symptom_text: str,
        present_symptoms: list[str],
        duration_days: int | None,
        fever_info: dict[str, Any],
    ) -> float:
        score = 0.0
        if age_years is not None:
            score += 0.2
        if symptom_text:
            score += 0.25
        if present_symptoms:
            score += 0.2
        if duration_days is not None:
            score += 0.15
        if fever_info.get("present"):
            if fever_info.get("duration_days") is not None:
                score += 0.1
            if fever_info.get("max_temp_c") is not None:
                score += 0.1
        else:
            score += 0.1
        return round(min(score, 1.0), 2)

    def _missing_factors(
        self,
        age_years: int | None,
        fever_info: dict[str, Any],
        duration_days: int | None,
        present_symptoms: list[str],
    ) -> list[str]:
        missing: list[str] = []
        if age_years is None:
            missing.append("age")
        if not present_symptoms:
            missing.append("symptoms")
        if duration_days is None:
            missing.append("symptom_duration")
        if fever_info.get("present"):
            if fever_info.get("duration_days") is None:
                missing.append("fever_duration_days")
            if fever_info.get("max_temp_c") is None:
                missing.append("fever_temperature")
        return missing
