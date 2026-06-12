"""Multi-engine document OCR — text layer, Tesseract, EasyOCR, PaddleOCR."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from backend.logger import get_logger
from backend.utils.lab_value_normalizer import clean_ocr_lab_text

logger = get_logger()

# Avoid OpenMP crash when torch + numpy load together (common on Windows).
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

_paddle_ocr = None
_easyocr_reader = None


def get_ocr_capabilities() -> dict[str, bool]:
    """Report which OCR engines are importable on this machine."""
    caps: dict[str, bool] = {
        "pdfplumber": _can_import("pdfplumber"),
        "pypdf": _can_import("pypdf"),
        "pymupdf": _can_import("fitz"),
        "tesseract": False,
        "easyocr": _can_import("easyocr"),
        "paddleocr": _can_import("paddleocr"),
    }
    try:
        import pytesseract
        import shutil

        if shutil.which("tesseract"):
            caps["tesseract"] = True
        else:
            # Common Windows install path
            for candidate in (
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ):
                if Path(candidate).is_file():
                    pytesseract.pytesseract.tesseract_cmd = candidate
                    caps["tesseract"] = True
                    break
    except ImportError:
        pass
    return caps


def _merge_ocr_texts(chunks: list[str]) -> str:
    """Combine OCR outputs — keep unique lines (best coverage for lab tables)."""
    merged_lines: dict[str, str] = {}
    for chunk in chunks:
        for line in chunk.splitlines():
            key = line.strip().lower()
            if len(key) < 2:
                continue
            if key not in merged_lines or len(line.strip()) > len(merged_lines[key]):
                merged_lines[key] = line.strip()
    return "\n".join(merged_lines.values())


def extract_pdf_text(path: Path) -> tuple[str, float, str]:
    """Extract text from PDF using all strategies and merge results."""
    chunks: list[str] = []
    methods: list[str] = []
    best_conf = 0.2

    for extractor in (
        _extract_pdf_pdfplumber,
        _extract_pdf_pypdf,
        _extract_pdf_pymupdf_text,
        _extract_pdf_page_ocr,
    ):
        text, confidence = extractor(path)
        if text.strip():
            chunks.append(text)
            methods.append(extractor.__name__.replace("_extract_pdf_", ""))
            best_conf = max(best_conf, confidence)

    if not chunks:
        logger.warning("PDF text extraction failed for %s", path)
        return "", 0.2, "none"

    merged = _merge_ocr_texts(chunks)
    text = merged if len(merged) >= max(len(c) for c in chunks) * 0.85 else max(chunks, key=len)
    method = "+".join(methods[:3]) if len(methods) > 1 else methods[0]
    logger.info("PDF text extracted via %s | chars=%d", method, len(text))
    return clean_ocr_lab_text(text), best_conf, method


def extract_image_text(path: Path) -> tuple[str, float, str]:
    """Run all image OCR engines and merge for maximum lab text recovery."""
    chunks: list[str] = []
    methods: list[str] = []
    best_conf = 0.2

    for extractor in (
        _extract_image_easyocr,
        _extract_image_tesseract,
        _extract_image_paddle,
    ):
        text, confidence = extractor(path)
        if text.strip():
            chunks.append(text)
            methods.append(extractor.__name__.replace("_extract_image_", ""))
            best_conf = max(best_conf, confidence)

    if not chunks:
        logger.warning("Image OCR failed for %s", path)
        return "", 0.2, "none"

    merged = _merge_ocr_texts(chunks)
    text = merged if len(merged) > len(max(chunks, key=len)) * 0.9 else max(chunks, key=len)
    method = "+".join(methods) if len(methods) > 1 else methods[0]
    logger.info("Image OCR via %s | chars=%d", method, len(text))
    return clean_ocr_lab_text(text), best_conf, method


def _can_import(module_name: str) -> bool:
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def _extract_pdf_pdfplumber(path: Path) -> tuple[str, float]:
    try:
        import pdfplumber

        chunks: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    chunks.append(page_text)
                tables = page.extract_tables() or []
                for table in tables:
                    for row in table:
                        if row:
                            chunks.append(" ".join(str(cell or "") for cell in row))
        text = "\n".join(chunks).strip()
        return text, 0.88 if text else 0.2
    except ImportError:
        return "", 0.2
    except Exception as exc:
        logger.warning("pdfplumber failed: %s", exc)
        return "", 0.2


def _extract_pdf_pypdf(path: Path) -> tuple[str, float]:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        chunks = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(chunks).strip()
        return text, 0.82 if text else 0.2
    except ImportError:
        return "", 0.2
    except Exception as exc:
        logger.warning("pypdf failed: %s", exc)
        return "", 0.2


def _extract_pdf_pymupdf_text(path: Path) -> tuple[str, float]:
    try:
        import fitz

        chunks: list[str] = []
        with fitz.open(path) as doc:
            for page in doc:
                page_text = page.get_text("text") or ""
                if page_text.strip():
                    chunks.append(page_text)
        text = "\n".join(chunks).strip()
        return text, 0.85 if text else 0.2
    except ImportError:
        return "", 0.2
    except Exception as exc:
        logger.warning("pymupdf text failed: %s", exc)
        return "", 0.2


def _extract_pdf_page_ocr(path: Path) -> tuple[str, float]:
    """Render each PDF page to image and run OCR (scanned documents)."""
    try:
        import fitz
    except ImportError:
        return "", 0.2

    chunks: list[str] = []
    try:
        with fitz.open(path) as doc:
            for page in doc:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp_path = Path(tmp.name)
                try:
                    pix = page.get_pixmap(dpi=300)
                    pix.save(str(tmp_path))
                    text, _conf, _method = extract_image_text(tmp_path)
                    if text.strip():
                        chunks.append(text)
                finally:
                    tmp_path.unlink(missing_ok=True)
        text = "\n".join(chunks).strip()
        return text, 0.74 if text else 0.2
    except Exception as exc:
        logger.warning("PDF page OCR failed: %s", exc)
        return "", 0.2


def _configure_tesseract() -> bool:
    try:
        import pytesseract
        import shutil

        if shutil.which("tesseract"):
            return True
        for candidate in (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ):
            if Path(candidate).is_file():
                pytesseract.pytesseract.tesseract_cmd = candidate
                return True
    except ImportError:
        return False
    return False


def _preprocess_for_ocr(path: Path) -> Path:
    """Enhance contrast and size for better OCR on lab documents."""
    try:
        from PIL import Image, ImageEnhance, ImageOps

        with Image.open(path) as img:
            img = img.convert("L")
            img = ImageOps.autocontrast(img)
            img = ImageEnhance.Sharpness(img).enhance(1.5)
            w, h = img.size
            if max(w, h) < 1800:
                scale = 1800 / max(w, h)
                img = img.resize((int(w * scale), int(h * scale)))
            out = path.with_suffix(".ocr.png")
            img.save(out)
            return out
    except Exception:
        return path


def _extract_image_tesseract(path: Path) -> tuple[str, float]:
    if not _configure_tesseract():
        return "", 0.2
    try:
        import pytesseract
        from PIL import Image

        prepared = _preprocess_for_ocr(path)
        text = pytesseract.image_to_string(
            Image.open(prepared),
            config="--psm 6",
        ).strip()
        if prepared != path and prepared.exists():
            prepared.unlink(missing_ok=True)
        return text, 0.76 if text else 0.2
    except Exception as exc:
        logger.warning("tesseract image OCR failed: %s", exc)
        return "", 0.2


def _extract_image_easyocr(path: Path) -> tuple[str, float]:
    global _easyocr_reader
    try:
        import easyocr
    except ImportError:
        return "", 0.2

    try:
        if _easyocr_reader is None:
            _easyocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        prepared = _preprocess_for_ocr(path)
        result = _easyocr_reader.readtext(str(prepared))
        if prepared != path and prepared.exists():
            prepared.unlink(missing_ok=True)
        lines = [str(item[1]).strip() for item in result if len(item) > 1 and item[1]]
        text = "\n".join(lines).strip()
        return text, 0.77 if text else 0.2
    except Exception as exc:
        logger.warning("EasyOCR failed: %s", exc)
        return "", 0.2


def _extract_image_paddle(path: Path) -> tuple[str, float]:
    global _paddle_ocr
    try:
        from paddleocr import PaddleOCR
    except ImportError:
        return "", 0.2

    try:
        if _paddle_ocr is None:
            _paddle_ocr = PaddleOCR(lang="en")
        result = _paddle_ocr.predict(str(path))
        lines: list[str] = []
        for item in result or []:
            if isinstance(item, dict):
                texts = item.get("rec_texts") or item.get("rec_text") or []
                if isinstance(texts, list):
                    lines.extend(str(t) for t in texts if t)
                elif texts:
                    lines.append(str(texts))
            elif isinstance(item, (list, tuple)) and len(item) > 1:
                block = item[1]
                if isinstance(block, (list, tuple)) and block:
                    lines.append(str(block[0]))
        text = "\n".join(lines).strip()
        if not text:
            # Legacy list format fallback
            legacy = _paddle_ocr.ocr(str(path))
            if legacy and legacy[0]:
                for line in legacy[0]:
                    if line and len(line) > 1 and line[1][0]:
                        lines.append(str(line[1][0]))
            text = "\n".join(lines).strip()
        return text, 0.78 if text else 0.2
    except Exception as exc:
        logger.warning("PaddleOCR failed: %s", exc)
        return "", 0.2
