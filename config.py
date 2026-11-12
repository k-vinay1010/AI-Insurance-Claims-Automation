from pathlib import Path
import os
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

APP_NAME = "AI Insurance Claims Processing Automation"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "insurance_claims")
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "").strip()
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "15"))
