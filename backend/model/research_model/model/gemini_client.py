"""
Netran AI — Stage 1: JD Research & Market Intelligence Engine
Module: gemini_client.py
Description: Class-based Gemini Interactions API client with REST fallback resilience.
"""

import logging

import requests

try:
    from .config import Stage1Config
except ImportError:
    try:
        from model.research_model.model.config import Stage1Config
    except ImportError:
        from config import Stage1Config

logger = logging.getLogger(__name__)


class GeminiClient:
    """Class-based Gemini API client using google-genai SDK Interactions API with REST fallback."""

    def __init__(self, config: Stage1Config | None = None):
        self.config = config or Stage1Config.from_env()

    @staticmethod
    def strip_fences(text: str) -> str:
        """Removes markdown code fences (```json ... ```) from model output."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:] if lines else lines
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            return "\n".join(lines).strip()
        return text

    def call(self, prompt: str, json_mode: bool = True, temperature: float = 0.2) -> str:
        """Calls Groq API (primary) with fallback to Gemini Interactions API / REST endpoint."""
        import os

        # ── Primary: Groq API ──────────────────────────────────────────────────
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        groq_model = os.getenv("GROQ_EVALUATION_MODEL", "openai/gpt-oss-120b")
        if groq_api_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_api_key)
                kwargs = {
                    "model": groq_model,
                    "messages": [
                        {"role": "system", "content": "You are an expert technical intelligence research system. Output valid JSON when required."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": temperature,
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                resp = client.chat.completions.create(**kwargs)
                content = resp.choices[0].message.content
                if content:
                    return self.strip_fences(content.strip())
            except Exception as groq_err:
                logger.warning(f"[ResearchModel] Groq call failed: {groq_err}. Falling back to Gemini...")

        api_key = self.config.gemini_api_key
        model = self.config.gemini_model or "gemini-3.6-flash"

        if not api_key and not groq_api_key:
            raise ValueError("Neither GROQ_API_KEY nor GEMINI_API_KEY is configured.")

        # ── Fallback 1: google-genai Interactions API ───────────────────────────
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            interaction = client.interactions.create(
                model=model,
                input=prompt,
                store=False,
            )
            text = interaction.output_text
            if text:
                return self.strip_fences(text.strip())
            raise ValueError("Empty output_text from Interactions API.")
        except ImportError:
            logger.warning("google-genai SDK unavailable. Falling back to REST endpoint...")
        except Exception as sdk_err:
            logger.warning(f"google.genai Interactions API call failed: {sdk_err}. Falling back to REST...")

        # ── Fallback: direct REST generateContent ───────────────────────────────
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
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

        return self.strip_fences(parts[0].get("text", "").strip())


# Backward compatibility global wrapper
def call_gemini_api(prompt: str, json_mode: bool = True, temperature: float = 0.2) -> str:
    return GeminiClient().call(prompt, json_mode=json_mode, temperature=temperature)
