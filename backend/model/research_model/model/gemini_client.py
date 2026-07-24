"""
Gemini client for the JD Research Model.

Uses the official google-genai SDK Interactions API:
    from google import genai
    client = genai.Client(api_key=...)
    interaction = client.interactions.create(model=..., input=...)

Falls back to a direct REST call if the SDK import fails (e.g. not yet installed).
"""

import requests
import logging
from model.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

MODEL = GEMINI_MODEL or "gemini-3.6-flash"


def _strip_fences(text: str) -> str:
    """Removes markdown code fences (```json ... ```) from model output."""
    if text.startswith("```"):
        lines = text.split("\n")
        # Drop first line (```json or ```) and last line if it's ```
        lines = lines[1:] if lines else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text


def call_gemini_api(prompt: str, json_mode: bool = True, temperature: float = 0.2) -> str:
    """
    Calls Gemini using the google-genai Interactions API.
    Falls back to direct REST if SDK is unavailable.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in .env")

    # ── Primary: google-genai Interactions API ──────────────────────────────
    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)

        interaction = client.interactions.create(
            model=MODEL,
            input=prompt,
            # store=False → no server-side history retention (free tier safe)
            store=False,
        )

        text = interaction.output_text
        if text:
            return text.strip()
        raise ValueError("Empty output_text from Interactions API.")

    except ImportError:
        logger.warning(
            "google-genai SDK not available (run: pip install -U google-genai). "
            "Falling back to REST endpoint..."
        )
    except Exception as sdk_err:
        logger.warning(
            f"google.genai Interactions API call failed: {sdk_err}. "
            "Falling back to REST endpoint..."
        )

    # ── Fallback: direct REST generateContent ───────────────────────────────
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature},
    }
    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()

    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini REST API returned no candidates.")

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise ValueError("Gemini REST API returned empty parts.")

    return _strip_fences(parts[0].get("text", "").strip())
