from backend.workers.celery_app import celery_app
from backend.ai.ocr.pipeline import ocr_pipeline
from backend.ai.imaging.vision import imaging_vision_engine
from backend.ai.nlp.clinical_nlp import clinical_nlp
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="process_document_task")
def process_document_task(self, file_path: str, file_type: str):
    logger.info(f"Processing document {file_path} of type {file_type}")
    try:
        if file_type == 'application/pdf':
            extracted_tables = ocr_pipeline.extract_tables_from_pdf(file_path)
            # Extracted tables processing here
            return {"status": "success", "tables": extracted_tables}
        elif file_type.startswith('image/'):
            text = ocr_pipeline.extract_text_from_image(file_path)
            nlp_result = clinical_nlp.process_text(text)
            return {"status": "success", "nlp_result": nlp_result}
        else:
            return {"status": "unsupported", "message": f"Type {file_type} not supported by OCR"}
    except Exception as e:
        logger.error(f"Error in process_document_task: {e}")
        return {"status": "error", "error": str(e)}

@celery_app.task(bind=True, name="process_imaging_task")
def process_imaging_task(self, file_path: str):
    logger.info(f"Processing imaging {file_path}")
    try:
        results = imaging_vision_engine.process_image(file_path)
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Error in process_imaging_task: {e}")
        return {"status": "error", "error": str(e)}
