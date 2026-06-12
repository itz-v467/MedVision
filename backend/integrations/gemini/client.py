import os
from google import genai
import logging

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY") or "dummy_key"
        if api_key == "dummy_key":
            logger.warning("GEMINI_API_KEY is not set. Using dummy key for initialization.")
        
        self.client = genai.Client(api_key=api_key)

    def generate_content(self, model: str, prompt: str, **kwargs):
        """
        Generate content using Gemini model.
        Supports structured output via kwargs (config=genai.types.GenerateContentConfig).
        """
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=kwargs.get("config")
        )
        return response

gemini_client = GeminiClient()
