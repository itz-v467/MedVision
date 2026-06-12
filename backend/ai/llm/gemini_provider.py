from backend.integrations.gemini.client import gemini_client
import json
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ClinicalSummaryOutput(BaseModel):
    summary: str
    key_findings: list[str]
    citations: list[str]

class GeminiProvider:
    def __init__(self):
        self.model_name = "gemini-2.5-pro"

    def generate_clinical_summary(self, patient_context: str, retrieved_evidence: str):
        prompt = f"""
        You are a highly capable AI physician assistant.
        Generate a clinical summary based on the following patient context and retrieved evidence.
        Provide your response as a JSON matching this schema:
        {{
            "summary": "Detailed clinical summary...",
            "key_findings": ["finding 1", "finding 2"],
            "citations": ["doc1_page2", "xray_id"]
        }}

        Context: {patient_context}
        Evidence: {retrieved_evidence}
        """
        try:
            response = gemini_client.generate_content(
                model=self.model_name,
                prompt=prompt,
                config={"response_mime_type": "application/json"}
            )
            if hasattr(response, 'text'):
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                return json.loads(text.strip())
            return {"summary": "Empty response", "key_findings": [], "citations": []}
        except Exception as e:
            logger.error(f"LLM Generation failed: {e}")
            return {"summary": "Error generating summary", "key_findings": [], "citations": []}

gemini_provider = GeminiProvider()
