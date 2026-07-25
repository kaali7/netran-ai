import os
import logging
from dotenv import load_dotenv

# Find .env in the backend root
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
dotenv_path = os.path.join(backend_dir, ".env")

load_dotenv(dotenv_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY is not set. API calls will fail.")
