import os
from dotenv import load_dotenv
from pathlib import Path

# Get the directory containing this file
current_dir = Path(__file__).parent

# Load environment variables from .env file in the same directory
env_path = current_dir / ".env"
load_dotenv(env_path)

# Google Gemini API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyDuk_NLrmbr8eZiVIKRhcqn9WfOSWJ2wR0")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set. Please set it in the .env file.")

# Print first few characters of API key for verification (for debugging)
print(f"API Key loaded (first 8 chars): {GOOGLE_API_KEY[:8]}...")

# Document Processing Configuration
SUPPORTED_DOCUMENT_TYPES = [".pdf", ".docx", ".txt"]
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB

# Risk Scoring Configuration
RISK_THRESHOLDS = {
    "low": 0.3,
    "medium": 0.6,
    "high": 0.8
}

# Document Analysis Configuration
REQUIRED_FIELDS = [
    "vendor_name",
    "gstin",
    "pan",
    "registration_date",
    "address",
    "contact_details"
]

# Risk Signal Weights
RISK_WEIGHTS = {
    "gstin_mismatch": 0.3,
    "missing_documents": 0.2,
    "irregular_billing": 0.25,
    "legal_disputes": 0.25
}

# Vector Store Configuration
CHROMA_PERSIST_DIRECTORY = str(current_dir / "data" / "chroma_db") 