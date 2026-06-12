import camelot
from paddleocr import PaddleOCR
import logging

logger = logging.getLogger(__name__)

class OCRPipeline:
    def __init__(self):
        # Initialize PaddleOCR (downloads models on first run if needed)
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en')

    def extract_text_from_image(self, image_path: str):
        try:
            result = self.ocr.ocr(image_path, cls=True)
            texts = [line[1][0] for line in result[0]] if result[0] else []
            return " ".join(texts)
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""

    def extract_tables_from_pdf(self, pdf_path: str):
        try:
            tables = camelot.read_pdf(pdf_path, pages='all')
            extracted = []
            for i, table in enumerate(tables):
                extracted.append(table.df.to_dict())
            return extracted
        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            return []
        
ocr_pipeline = OCRPipeline()
