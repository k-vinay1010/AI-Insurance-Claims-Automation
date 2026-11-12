# AI Insurance Claims Processing Automation

A local prototype for extracting structured information from insurance claim documents and preparing them for human review.

## Features

- PDF text extraction with OCR fallback for scanned PDFs.
- OCR for PNG, JPG, JPEG and TIFF images.
- Rule-based extraction of patient name, policy number, hospital, amount, date and diagnosis.
- Required-field and amount validation.
- Optional Gemini 2.5 Flash claim summary.
- SQLite persistence by default; optional MongoDB mirror.
- Streamlit user interface.
- FastAPI REST API.
- CSV export and basic tests.

## Important limitations

This is a portfolio prototype using synthetic data. It does not approve or reject claims, determine coverage, detect fraud, provide medical advice, or connect to real hospital/insurer portals. All outputs require human verification. Do not upload real patient or insurance documents.

## Requirements

- Python 3.10 or newer recommended.
- Tesseract OCR installed separately for scanned PDFs and image OCR.
- Gemini API key optional.
- MongoDB connection optional.

## Windows setup (VS Code terminal)

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` if needed. Set `TESSERACT_CMD` to your installed Tesseract executable. Add `GEMINI_API_KEY` only if you want Gemini summaries. SQLite works without MongoDB.

## Run the Streamlit app

From the project root:

```powershell
streamlit run frontend/app.py
```

Open the local URL shown in the terminal (normally http://localhost:8501).

## Run the FastAPI backend

Open another terminal, activate the same environment, then:

```powershell
uvicorn backend.main:app --reload
```

API documentation: http://127.0.0.1:8000/docs

## API endpoints

- `GET /health` - health check.
- `POST /claims` - upload a claim document as multipart form data; optional `use_ai` query parameter.
- `GET /claims` - list stored claims.
- `GET /claims/{claim_id}` - retrieve one claim.
- `DELETE /claims/{claim_id}` - delete one claim.

Example upload using curl:

```bash
curl -X POST "http://127.0.0.1:8000/claims?use_ai=false" \
  -F "file=@sample_claim.pdf"
```

## Run tests

```powershell
pytest -q
```

## Synthetic sample

A synthetic text example is available at `documents/sample_claims/sample_claim.txt`. To test OCR, create a PDF or image containing the same synthetic fields, or use a sample claim document with clearly printed labels.

## GitHub

Before publishing:
1. Confirm `.env` is not tracked.
2. Do not commit real patient data, API keys, or private documents.
3. Commit only synthetic sample data.
4. Add screenshots of the working app after testing it locally.
