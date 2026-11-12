from pathlib import Path
import io
import re
from PIL import Image
import fitz
import pytesseract
from backend.config import TESSERACT_CMD

if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}

def extract_text(filename: str, content: bytes) -> tuple[str, str]:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type. Upload PDF, PNG, JPG, JPEG, or TIFF.")
    if ext == ".pdf":
        doc = fitz.open(stream=content, filetype="pdf")
        pages = [page.get_text("text") for page in doc]
        text = "\n".join(pages).strip()
        if len(text) >= 20:
            return text, "PDF text extraction"
        # Scanned PDF fallback: render pages and OCR them.
        ocr_pages = []
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.open(io.BytesIO(pix.tobytes("png")))
            ocr_pages.append(pytesseract.image_to_string(image))
        return "\n".join(ocr_pages).strip(), "OCR on scanned PDF"
    image = Image.open(io.BytesIO(content)).convert("RGB")
    return pytesseract.image_to_string(image).strip(), "OCR image"

def extract_fields(text: str) -> dict:
    normalized = re.sub(r"[ \t]+", " ", text)
    patterns = {
        "patient_name": [
            r"(?:patient\s*name|name\s*of\s*patient)\s*[:\-]\s*([A-Za-z][A-Za-z .'-]{1,70})",
            r"(?:insured\s*name)\s*[:\-]\s*([A-Za-z][A-Za-z .'-]{1,70})",
        ],
        "policy_number": [
            r"(?:policy\s*(?:number|no\.?|#)|policy\s*id)\s*[:\-]\s*([A-Za-z0-9/-]{4,35})",
        ],
        "hospital_name": [
            r"(?:hospital\s*name|provider\s*name)\s*[:\-]\s*([A-Za-z0-9 &.,'-]{2,80})",
        ],
        "claim_amount": [
            r"(?:claim\s*amount|amount\s*claimed|total\s*amount)\s*[:\-]?\s*(?:INR|Rs\.?|₹)?\s*([0-9,]+(?:\.[0-9]{1,2})?)",
        ],
        "claim_date": [
            r"(?:claim\s*date|date\s*of\s*claim|admission\s*date)\s*[:\-]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})",
        ],
        "diagnosis": [
            r"(?:diagnosis| ailment|disease)\s*[:\-]\s*([A-Za-z0-9 ,().'-]{2,100})",
        ],
    }
    result = {key: None for key in patterns}
    for field, expressions in patterns.items():
        for expression in expressions:
            match = re.search(expression, normalized, flags=re.IGNORECASE)
            if match:
                value = match.group(1).strip(" \n\t:;,.")
                if field == "claim_amount":
                    try:
                        value = float(value.replace(",", ""))
                    except ValueError:
                        continue
                result[field] = value
                break
    return result
