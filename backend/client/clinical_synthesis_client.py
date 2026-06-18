"""Generate doctor-style clinical synthesis from global encounter context."""

from __future__ import annotations

import json
from typing import Any

from backend.config import get_settings
from backend.core.singleton import SingletonMixin
from backend.logger import get_logger

logger = get_logger()

SYNTHESIS_SYSTEM_PROMPT = """You are a senior clinical decision-support physician assistant.
Review ALL available data like a doctor at morning rounds:
1. Demographics: age, gender, elderly/pediatric risk
2. Symptom history: onset, duration, fever days, temperature, cough type
3. Objective labs and vitals
4. Imaging findings
5. Disease pattern matches and correlation cards
6. Synthesize working diagnosis, differential, care plan, and consult urgency

Output ONLY valid JSON with these keys:
- patient_summary: 2-4 short sentences in plain language for the patient
- physician_summary: concise clinical paragraph for the treating doctor
- clinical_factors_review: narrative explicitly citing age, fever duration, symptom days, and reports reviewed
- correlation_narrative: how symptoms, labs, and imaging relate
- leading_diagnosis: { "condition": str, "confidence": "high"|"moderate"|"low", "rationale": str }
- differential: array of { "condition", "likelihood", "supporting": [str], "against": [str] } (2-4 items)
- possible_diseases_report: array of { "rank": int, "condition": str, "likelihood": "high"|"moderate"|"low", "key_evidence": [str], "missing_data": [str] }
- root_cause_analysis: professional paragraph on most likely underlying cause/process
- recommended_workup: array of short next-step strings
- care_plan: {
    "status": "pending_physician_approval",
    "medications": [{ "name": str, "purpose": str, "typical_dose_range": str, "notes": "physician must confirm" }],
    "otc_options": [str],
    "recovery": {
      "foods_to_eat": [str],
      "foods_to_avoid": [str],
      "activities_to_avoid": [str],
      "hydration_rest": str
    },
    "monitoring": [str]
  }
- consult_recommendation: { "urgency": "same_day"|"within_24h"|"routine", "reason": str, "in_app_consult": true }
- disclaimer: AI-assisted only; physician must confirm; medications are suggestions not prescriptions

Use "most consistent with" language. Medications are suggestions_for_physician only."""

REQUIRED_KEYS = (
    "patient_summary",
    "physician_summary",
    "clinical_factors_review",
    "correlation_narrative",
    "leading_diagnosis",
    "differential",
    "possible_diseases_report",
    "root_cause_analysis",
    "recommended_workup",
    "care_plan",
    "consult_recommendation",
    "disclaimer",
)


class ClinicalSynthesisClient(SingletonMixin):
    """Produce structured patient + physician synthesis via LLM or rules."""

    def __init__(self) -> None:
        if self._initialized:
            return
        self._settings = get_settings()
        self._initialized = True

    def synthesize(
        self,
        global_context: dict[str, Any],
        grounded_chunks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Return structured clinical synthesis dict."""
        if self._settings.openai_enabled:
            result = self._via_openai(global_context, grounded_chunks or [])
            if result:
                return result

        if self._settings.gemini_enabled:
            result = self._via_gemini(global_context, grounded_chunks or [])
            if result:
                return result

        return self._rule_based_synthesis(global_context)

    def _via_openai(
        self, global_context: dict[str, Any], grounded_chunks: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        try:
            from backend.client.openai_client import get_openai_client

            client = get_openai_client()
            prompt = self._build_user_prompt(global_context, grounded_chunks)
            data = client.extract_structured_json(
                SYNTHESIS_SYSTEM_PROMPT, prompt, max_tokens=2200
            )
            return self._normalize(data, engine="openai")
        except Exception as exc:
            logger.warning("OpenAI clinical synthesis failed: %s", exc)
            return None

    def _via_gemini(
        self, global_context: dict[str, Any], grounded_chunks: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        try:
            from google import genai

            prompt = (
                f"{SYNTHESIS_SYSTEM_PROMPT}\n\n"
                f"{self._build_user_prompt(global_context, grounded_chunks)}"
            )
            client = genai.Client(api_key=self._settings.gemini_api_key)
            response = client.models.generate_content(
                model=self._settings.gemini_llm_model,
                contents=prompt,
            )
            text = (getattr(response, "text", None) or "").strip()
            if text.startswith("```"):
                parts = text.split("```")
                text = parts[1] if len(parts) > 1 else text
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text)
            return self._normalize(data, engine="gemini")
        except Exception as exc:
            logger.warning("Gemini clinical synthesis failed: %s", exc)
            return None

    def _build_user_prompt(
        self, global_context: dict[str, Any], grounded_chunks: list[dict[str, Any]]
    ) -> str:
        chunk_text = "\n".join(
            f"- [{c.get('source_type', 'source')}] {(c.get('chunk_text') or '')[:350]}"
            for c in (grounded_chunks or [])[:6]
        )
        return (
            "Synthesize this unified clinical case:\n\n"
            f"{json.dumps(global_context, default=str)[:14000]}\n\n"
            f"Retrieved evidence:\n{chunk_text or 'None'}"
        )

    def _normalize(self, data: Any, *, engine: str) -> dict[str, Any] | None:
        if not isinstance(data, dict):
            return None
        for key in REQUIRED_KEYS:
            if key == "differential":
                data.setdefault(key, [])
            elif key == "possible_diseases_report":
                data.setdefault(key, [])
            elif key == "recommended_workup":
                data.setdefault(key, [])
            elif key == "care_plan":
                data.setdefault(key, self._default_care_plan())
            elif key == "consult_recommendation":
                data.setdefault(key, {"urgency": "routine", "reason": "", "in_app_consult": True})
            elif key == "leading_diagnosis":
                if not isinstance(data.get(key), dict):
                    data[key] = {
                        "condition": str(data.get(key) or "Under evaluation"),
                        "confidence": "low",
                        "rationale": "",
                    }
            else:
                data.setdefault(key, "")

        if not isinstance(data.get("differential"), list):
            data["differential"] = []
        if not isinstance(data.get("possible_diseases_report"), list):
            data["possible_diseases_report"] = []
        if not isinstance(data.get("recommended_workup"), list):
            data["recommended_workup"] = []
        care = data.get("care_plan")
        if not isinstance(care, dict):
            data["care_plan"] = self._default_care_plan()
        else:
            care.setdefault("status", "pending_physician_approval")
            care.setdefault("medications", [])
            care.setdefault("otc_options", [])
            care.setdefault("recovery", {
                "foods_to_eat": [],
                "foods_to_avoid": [],
                "activities_to_avoid": [],
                "hydration_rest": "",
            })
            care.setdefault("monitoring", [])

        data["engine"] = engine
        return data

    def _default_care_plan(self) -> dict[str, Any]:
        return {
            "status": "pending_physician_approval",
            "medications": [],
            "otc_options": [],
            "recovery": {
                "foods_to_eat": [],
                "foods_to_avoid": [],
                "activities_to_avoid": [],
                "hydration_rest": "",
            },
            "monitoring": [],
        }

    def _rule_based_synthesis(self, ctx: dict[str, Any]) -> dict[str, Any]:
        """Deterministic synthesis when no LLM is available."""
        factors = ctx.get("clinical_factors") or {}
        demographics = factors.get("demographics") or {}
        factor_symptoms = factors.get("symptoms") or {}
        symptoms = ctx.get("symptoms") or {}
        chief = factor_symptoms.get("chief_complaint") or symptoms.get("chief_complaint") or ""
        risk = symptoms.get("risk_level") or "low"
        labs = ctx.get("labs") or {}
        abnormal = labs.get("abnormal") or []
        imaging_flags = ctx.get("imaging_flags") or {}
        correlation = ctx.get("correlation") or {}
        cards = correlation.get("cards") or []
        patterns = (ctx.get("pattern_matches") or {}).get("pattern_matches") or []

        age = demographics.get("age_years")
        fever = factor_symptoms.get("fever") or {}
        duration = factor_symptoms.get("symptom_duration_days")

        opacity = imaging_flags.get("opacity")
        has_respiratory = any(
            s in (factor_symptoms.get("present_symptoms") or [])
            for s in ("fever", "cough", "breathlessness")
        )

        leading = patterns[0]["condition"] if patterns else "Clinical evaluation needed"
        confidence = "moderate" if patterns and patterns[0].get("score", 0) >= 0.6 else "low"
        rationale_parts: list[str] = []

        if age is not None:
            rationale_parts.append(f"Patient age {age} years")
        if fever.get("duration_days"):
            rationale_parts.append(f"fever for {fever['duration_days']} day(s)")
        if duration:
            rationale_parts.append(f"symptoms for {duration} day(s)")
        if demographics.get("elderly"):
            rationale_parts.append("older adult — higher complication risk")

        differential = [
            {
                "condition": p["condition"],
                "likelihood": "high" if p.get("score", 0) >= 0.7 else "moderate",
                "supporting": p.get("evidence_factors") or [],
                "against": ["Requires physician exam for confirmation"],
            }
            for p in patterns[:4]
        ]

        possible_diseases_report = [
            {
                "rank": idx + 1,
                "condition": p["condition"],
                "likelihood": "high" if p.get("score", 0) >= 0.7 else "moderate",
                "key_evidence": p.get("evidence_factors") or [],
                "missing_data": factors.get("missing_factors") or [],
            }
            for idx, p in enumerate(patterns[:4])
        ]

        card_notes = "; ".join(f"{c.get('label')}: {c.get('value')}" for c in cards[:3])
        factors_review = ". ".join(rationale_parts) or "Limited structured history available."
        correlation_narrative = card_notes or (
            "Correlate symptoms, labs, and imaging at bedside."
        )

        patient_summary = (
            f"We reviewed your symptoms"
            f"{f' (about {duration} days)' if duration else ''}"
            f"{', lab results,' if abnormal else ''}"
            f"{', and chest X-ray' if imaging_flags else ''}. "
            f"The pattern is most consistent with: {leading}. "
            "Your doctor will confirm the next steps."
        )
        physician_summary = (
            f"Case synthesis: {factors_review}. "
            f"Working impression: {leading} ({confidence} confidence). "
            f"{correlation_narrative} Triage risk: {risk}. Physician confirmation required."
        )

        workup = ["Physician history and physical examination"]
        if imaging_flags:
            workup.append("Radiologist review of chest X-ray")
        if abnormal:
            workup.append("Repeat or trend abnormal laboratory values")
        if has_respiratory:
            workup.append("Vitals, oxygen saturation, and respiratory exam")

        recovery = self._recovery_for_condition(leading, abnormal)
        medications = self._medication_suggestions(leading)
        consult_urgency = "within_24h" if has_respiratory and opacity else "routine"
        if risk in {"emergency", "high"}:
            consult_urgency = "same_day"

        return {
            "patient_summary": patient_summary,
            "physician_summary": physician_summary,
            "clinical_factors_review": factors_review,
            "correlation_narrative": correlation_narrative,
            "leading_diagnosis": {
                "condition": leading,
                "confidence": confidence,
                "rationale": factors_review,
            },
            "differential": differential,
            "possible_diseases_report": possible_diseases_report,
            "root_cause_analysis": (
                f"Integrating age, symptom duration, labs, and imaging, the working "
                f"impression is {leading}. {correlation_narrative}"
            ),
            "recommended_workup": workup,
            "care_plan": {
                "status": "pending_physician_approval",
                "medications": medications,
                "otc_options": ["Acetaminophen for fever/pain if no contraindications (OTC)"],
                "recovery": recovery,
                "monitoring": [
                    "Check temperature twice daily",
                    "Return urgently if breathing worsens or oxygen feels low",
                ],
            },
            "consult_recommendation": {
                "urgency": consult_urgency,
                "reason": f"Pattern suggests {leading}; physician should confirm and treat.",
                "in_app_consult": True,
            },
            "disclaimer": (
                "AI-assisted synthesis only — not a diagnosis or prescription. "
                "All medications are suggestions for physician approval."
            ),
            "engine": "rules",
        }

    def _recovery_for_condition(
        self, condition: str, abnormal: list[dict[str, Any]]
    ) -> dict[str, Any]:
        lowered = condition.lower()
        if "pneumonia" in lowered or "respiratory" in lowered or "opacity" in lowered:
            return {
                "foods_to_eat": [
                    "Warm soups and broths",
                    "Soft fruits and vegetables",
                    "Plenty of fluids",
                ],
                "foods_to_avoid": [
                    "Alcohol",
                    "Heavy greasy foods",
                    "Very cold drinks if they trigger cough",
                ],
                "activities_to_avoid": [
                    "Strenuous exercise until fever resolves",
                    "Smoking or smoke exposure",
                ],
                "hydration_rest": "Rest, drink fluids regularly, and sleep adequately.",
            }
        if "bilirubin" in " ".join(
            str(b.get("name", "")) for b in abnormal
        ).lower() or "hepatobiliary" in lowered:
            return {
                "foods_to_eat": ["Lean proteins", "Fruits and vegetables", "Adequate hydration"],
                "foods_to_avoid": ["Alcohol", "Fatty fried foods", "Excess processed sugar"],
                "activities_to_avoid": ["Alcohol", "Unnecessary hepatotoxic supplements"],
                "hydration_rest": "Hydrate well; avoid alcohol until physician review.",
            }
        return {
            "foods_to_eat": ["Balanced meals", "Fruits and vegetables", "Adequate water"],
            "foods_to_avoid": ["Alcohol until evaluated", "Excess processed food"],
            "activities_to_avoid": ["Overexertion until symptoms improve"],
            "hydration_rest": "Rest and maintain good hydration.",
        }

    def _medication_suggestions(self, condition: str) -> list[dict[str, Any]]:
        lowered = condition.lower()
        if "pneumonia" in lowered or ("respiratory" in lowered and "opacity" in lowered):
            return [
                {
                    "name": "Antibiotic therapy (e.g. amoxicillin-clavulanate or azithromycin)",
                    "purpose": "Treat suspected bacterial lower respiratory infection",
                    "typical_dose_range": "Per local guidelines — physician must select",
                    "notes": "suggestion_for_physician — confirm allergy history and local resistance patterns",
                },
            ]
        return []


def get_clinical_synthesis_client() -> ClinicalSynthesisClient:
    """Return clinical synthesis singleton."""
    return ClinicalSynthesisClient()
