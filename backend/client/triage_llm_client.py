"""Multi-provider LLM client for symptom triage conversations."""

from __future__ import annotations

import json
from typing import Any

from backend.config import get_settings
from backend.constants.triage_policy import TRIAGE_SYSTEM_PROMPT, TRIAGE_DISCLAIMER
from backend.core.singleton import SingletonMixin
from backend.logger import get_logger
from backend.service.triage_conversation_engine import generate_guided_triage_reply

logger = get_logger()


class TriageLlmClient(SingletonMixin):
    """Generate healthcare triage replies via OpenAI, Gemini, or guided fallback."""

    def __init__(self) -> None:
        if self._initialized:
            return
        self._settings = get_settings()
        self._openai_client: Any = None
        self._initialized = True

    def generate_reply(
        self,
        messages: list[dict[str, str]],
        context: dict[str, Any],
        assessment: dict[str, Any],
    ) -> tuple[str, str]:
        """Return (reply_text, assistant_mode)."""
        if self._settings.openai_enabled:
            reply = self._via_openai(messages, context, assessment)
            if reply:
                return reply, "openai"

        if self._settings.gemini_enabled:
            reply = self._via_gemini(messages, context, assessment)
            if reply:
                return reply, "gemini"

        return (
            generate_guided_triage_reply(messages, context, assessment),
            "guided",
        )

    def _via_openai(
        self,
        messages: list[dict[str, str]],
        context: dict[str, Any],
        assessment: dict[str, Any],
    ) -> str | None:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self._settings.openai_api_key)
            prompt_messages = [{"role": "system", "content": TRIAGE_SYSTEM_PROMPT}]
            prompt_messages.append(
                {
                    "role": "system",
                    "content": self._context_block(context, assessment),
                }
            )
            for msg in messages[-12:]:
                role = msg.get("role", "user")
                if role == "patient":
                    role = "user"
                prompt_messages.append(
                    {
                        "role": role,
                        "content": msg.get("message_text") or msg.get("content") or "",
                    }
                )
            response = client.chat.completions.create(
                model=self._settings.openai_llm_model,
                messages=prompt_messages,
                temperature=0.35,
                max_tokens=550,
            )
            content = (response.choices[0].message.content or "").strip()
            return content or None
        except Exception as exc:
            logger.warning("OpenAI triage reply failed: %s", exc)
            return None

    def _via_gemini(
        self,
        messages: list[dict[str, str]],
        context: dict[str, Any],
        assessment: dict[str, Any],
    ) -> str | None:
        try:
            from google import genai

            transcript = []
            for msg in messages[-14:]:
                role = (msg.get("role") or "").lower()
                speaker = "Patient" if role in {"user", "patient"} else "Assistant"
                text = (msg.get("message_text") or msg.get("content") or "").strip()
                if text:
                    transcript.append(f"{speaker}: {text}")

            prompt = f"""{TRIAGE_SYSTEM_PROMPT}

Patient context:
{self._context_block(context, assessment)}

Conversation transcript:
{chr(10).join(transcript)}

Write the Assistant's next reply only. Requirements:
- Sound like a compassionate healthcare intake nurse, not a generic bot.
- Acknowledge what the patient just said in your own words.
- Ask 1–2 specific follow-up questions about duration, severity, red flags, meds, or allergies.
- Give brief triage-appropriate next-step guidance aligned with risk level (no diagnosis, no prescriptions).
- End with a short physician-review reminder.
- Maximum 130 words."""

            client = genai.Client(api_key=self._settings.gemini_api_key)
            response = client.models.generate_content(
                model=self._settings.gemini_llm_model,
                contents=prompt,
            )
            text = getattr(response, "text", None) or ""
            text = text.strip()
            if text and TRIAGE_DISCLAIMER not in text:
                text = f"{text} {TRIAGE_DISCLAIMER}"
            return text or None
        except Exception as exc:
            logger.warning("Gemini triage reply failed: %s", exc)
            return None

    def _context_block(self, context: dict[str, Any], assessment: dict[str, Any]) -> str:
        missing = assessment.get("missing_factors") or []
        completeness = assessment.get("data_completeness")
        missing_line = (
            f"Missing clinical factors to collect: {', '.join(missing)}\n"
            if missing
            else ""
        )
        completeness_line = (
            f"Data completeness: {completeness}\n" if completeness is not None else ""
        )
        return (
            f"Patient: {context.get('patient_name', 'Unknown')} | "
            f"Age: {context.get('patient_age', '—')} | "
            f"Gender: {context.get('patient_gender', '—')}\n"
            f"Risk level: {assessment.get('risk_level')} | "
            f"Disposition: {assessment.get('recommended_disposition')}\n"
            f"{completeness_line}"
            f"{missing_line}"
            f"Rationale: {json.dumps(assessment.get('rationale', []))}\n"
            f"Encounter context: {json.dumps({k: v for k, v in context.items() if k not in {'nlp_entities', 'imaging_findings'}}, default=str)[:1200]}"
        )


def get_triage_llm_client() -> TriageLlmClient:
    """Return triage LLM client singleton."""
    return TriageLlmClient()
