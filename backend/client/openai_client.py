"""OpenAI client for clinical summary generation."""

from __future__ import annotations

from typing import Any

from backend.config import get_settings
from backend.core.singleton import SingletonMixin
from backend.logger import get_logger

logger = get_logger()

SUMMARY_SYSTEM_PROMPT = (
    "You are a clinical decision support assistant. "
    "Produce concise, evidence-grounded summaries for physician review. "
    "Never provide definitive diagnoses. Always note that physician review is required."
)


class OpenAiClient(SingletonMixin):
    """Wraps OpenAI chat completions for summary text."""

    def __init__(self) -> None:
        """Initialize OpenAI settings."""
        if self._initialized:
            return
        self._settings = get_settings()
        self._client: Any = None
        self._initialized = True

    @property
    def is_enabled(self) -> bool:
        """Return True when API key is configured."""
        return self._settings.openai_enabled

    def _ensure_client(self) -> None:
        """Lazy-create OpenAI SDK client."""
        if self._client is not None:
            return
        from openai import OpenAI

        self._client = OpenAI(api_key=self._settings.openai_api_key)

    def generate_summary(
        self,
        context: dict[str, Any],
        grounded_chunks: list[dict[str, Any]],
    ) -> str:
        """Generate physician-review summary from multimodal context."""
        if not self.is_enabled:
            return self._fallback_summary(context, grounded_chunks)

        prompt = self._build_prompt(context, grounded_chunks)
        try:
            self._ensure_client()
            response = self._client.chat.completions.create(
                model=self._settings.openai_llm_model,
                messages=[
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=500,
            )
            content = response.choices[0].message.content or ""
            return content.strip() or self._fallback_summary(context, grounded_chunks)
        except Exception as exc:
            logger.warning("OpenAI summary generation failed: %s", exc)
            return self._fallback_summary(context, grounded_chunks)

    def _build_prompt(
        self,
        context: dict[str, Any],
        grounded_chunks: list[dict[str, Any]],
    ) -> str:
        """Build user prompt from pipeline outputs."""
        chunk_text = "\n".join(
            (
                f"- [{chunk.get('source_type', 'source')}] "
                f"{chunk.get('chunk_text', '')[:400]}"
            )
            for chunk in grounded_chunks[:5]
        )
        intro = (
            "Generate a structured clinical summary for physician review "
            "using this data.\n\n"
        )
        closing = (
            "Include key findings, suggested correlation, "
            "and explicit physician review note."
        )
        return (
            f"{intro}"
            f"OCR/Labs: {context.get('ocr', {})}\n"
            f"NLP entities: {context.get('nlp', {})}\n"
            f"Imaging findings: {context.get('imaging', {})}\n"
            f"Correlation score: {context.get('correlation', {})}\n\n"
            f"Retrieved evidence chunks:\n{chunk_text or 'None'}\n\n"
            f"{closing}"
        )

    def _fallback_summary(
        self,
        context: dict[str, Any],
        grounded_chunks: list[dict[str, Any]],
    ) -> str:
        """Template summary when OpenAI is unavailable."""
        imaging = context.get("imaging", {}).get("findings", {})
        detected = [
            name
            for name, data in imaging.items()
            if isinstance(data, dict) and data.get("detected")
        ]
        ocr = context.get("ocr", {}).get("structured_data", {})
        biomarkers = ocr.get("biomarkers", [])
        nlp_entities = context.get("nlp", {}).get("entities", {})
        diseases = nlp_entities.get("diseases", [])

        parts = ["AI-assisted summary:"]
        if detected:
            parts.append(f"Imaging flags: {', '.join(detected)}.")
        if biomarkers:
            marker_names = ", ".join(item.get("name", "") for item in biomarkers[:3])
            parts.append(f"Lab markers extracted: {marker_names}.")
        if diseases:
            parts.append(f"NLP entities include: {', '.join(diseases)}.")
        parts.append("Correlate with clinical presentation.")
        parts.append("Physician review required before finalization.")
        if grounded_chunks:
            parts.append(
                f"Grounded on {len(grounded_chunks)} vector-retrieved sources."
            )
        return " ".join(parts)


def get_openai_client() -> OpenAiClient:
    """Return OpenAI client singleton."""
    return OpenAiClient()
