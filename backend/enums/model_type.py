"""AI model type constants."""

from enum import Enum


class ModelType(str, Enum):
    """Registered model categories."""

    OCR = "OCR"
    NLP = "NLP"
    IMAGING = "IMAGING"
    RAG = "RAG"
    CORRELATION = "CORRELATION"
    EXPLAINABILITY = "EXPLAINABILITY"
