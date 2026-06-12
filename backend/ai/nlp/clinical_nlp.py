import spacy
import logging

logger = logging.getLogger(__name__)

class ClinicalNLP:
    def __init__(self):
        try:
            # Load the SciSpacy model (en_core_sci_sm) using spacy directly.
            # The full scispacy package is incompatible with Python 3.13 without a C++ compiler,
            # so we only use the model for entity extraction, avoiding the UMLS linker.
            self.nlp = spacy.load("en_core_sci_sm")
        except Exception as e:
            logger.warning(f"Failed to load scispacy model. Please ensure it's installed. {e}")
            self.nlp = None

    def process_text(self, text: str):
        if not self.nlp:
            return {"entities": []}
        try:
            doc = self.nlp(text)
            entities = []
            
            for ent in doc.ents:
                ent_data = {"text": ent.text, "label": ent.label_}
                entities.append(ent_data)
            return {"entities": entities}
        except Exception as e:
            logger.error(f"NLP processing failed: {e}")
            return {"entities": []}
        
clinical_nlp = ClinicalNLP()
