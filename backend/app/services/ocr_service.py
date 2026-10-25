import logging
from typing import Optional
from PIL import Image

logger = logging.getLogger("sovereign_ai.ocr")

# Flag to track whether pytesseract is available and working
_ocr_available: Optional[bool] = None


def check_ocr_availability() -> bool:
    global _ocr_available
    if _ocr_available is not None:
        return _ocr_available

    try:
        import pytesseract
        # Try a quick test on a tiny blank image
        test_img = Image.new("RGB", (30, 30), color="white")
        pytesseract.image_to_string(test_img)
        _ocr_available = True
        logger.info("Local Tesseract OCR engine detected and operational.")
    except Exception as e:
        _ocr_available = False
        logger.warning(f"Local Tesseract OCR engine not available ({e}). Scanned page OCR will fall back to multimodal processing.")

    return _ocr_available


def run_ocr(image: Image.Image) -> str:
    """Run local OCR on a PIL Image if available, otherwise return empty string."""
    if not check_ocr_availability():
        return ""

    try:
        import pytesseract
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        logger.warning(f"OCR execution failed on page/image: {e}")
        return ""
