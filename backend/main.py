from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.config import APP_NAME, MAX_UPLOAD_MB
from backend.database import init_db, list_claims, get_claim, delete_claim
from backend.claim_service import process_document

app = FastAPI(title=APP_NAME, version="1.0.0",
              description="Document extraction and human-review support. Not an automated claim decision system.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME}

@app.post("/claims")
async def create_claim(file: UploadFile = File(...), use_ai: bool = True):
    content = await file.read()
    if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_UPLOAD_MB} MB limit")
    try:
        result = process_document(file.filename or "upload", content, use_ai=use_ai)
        safe_result = {k: v for k, v in result.items() if k != "extracted_text"}
        return safe_result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}")

@app.get("/claims")
def claims():
    return list_claims()

@app.get("/claims/{claim_id}")
def claim_detail(claim_id: str):
    result = get_claim(claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Claim not found")
    return result

@app.delete("/claims/{claim_id}")
def remove_claim(claim_id: str):
    if not delete_claim(claim_id):
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"deleted": True, "claim_id": claim_id}
