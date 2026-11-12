from uuid import uuid4
from backend.document_parser import extract_text, extract_fields
from backend.database import save_claim

REQUIRED_FIELDS = ["patient_name", "policy_number", "hospital_name", "claim_amount", "claim_date"]

def validate_claim(fields: dict) -> list[str]:
    flags = []
    for field in REQUIRED_FIELDS:
        if fields.get(field) in (None, ""):
            flags.append(f"Missing required field: {field.replace('_', ' ')}")
    amount = fields.get("claim_amount")
    if amount is not None and amount <= 0:
        flags.append("Claim amount must be greater than zero")
    if amount is not None and amount > 10_000_000:
        flags.append("Claim amount is unusually high; manual verification required")
    return flags

def process_document(filename: str, content: bytes, use_ai: bool = True) -> dict:
    text, extraction_method = extract_text(filename, content)
    fields = extract_fields(text)
    flags = validate_claim(fields)
    summary = create_summary(fields, flags, text, use_ai=use_ai)
    claim = {
        "claim_id": str(uuid4()),
        **fields,
        "extracted_text": text,
        "summary": summary,
        "status": "Needs review" if flags else "Extracted - pending human review",
        "flags": flags,
        "source_filename": filename,
        "extraction_method": extraction_method,
    }
    save_claim(claim)
    return claim

def create_summary(fields: dict, flags: list[str], text: str, use_ai: bool = True) -> str:
    if use_ai:
        try:
            from backend.llm_service import generate_claim_summary
            ai_summary = generate_claim_summary(fields, flags, text)
            if ai_summary:
                return ai_summary
        except Exception:
            pass
    present = [f"{k.replace('_', ' ').title()}: {v}" for k, v in fields.items() if v is not None]
    details = "; ".join(present) if present else "No structured claim fields could be identified."
    review = "Manual review required: " + "; ".join(flags) if flags else "All configured required fields were extracted; verify against the source document."
    return f"Claim summary (rule-based): {details}. {review}"
