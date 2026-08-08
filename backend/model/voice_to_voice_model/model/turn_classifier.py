"""
Turn Classifier Module (Case 3 Hybrid Architecture)
Determines whether candidate speech is a complete thought or an interrupted pause/thinking state.
Tier 1: Ultra-fast regex check (0ms).
Tier 2: Qwen2.5:1.5B classification via local Ollama API (~80-120ms fallback).
"""

import os
import requests

THINKING_FILLER_WORDS = {
    "and", "because", "so", "but", "or", "uh", "um", "like", "with",
    "that", "which", "if", "then", "when", "where", "also", "for", "to",
    "hmm", "ah", "well", "basically", "actually", "honestly", "mean",
    "guess", "suppose", "think", "maybe", "probably", "since", "while",
    "though", "although", "unless", "until", "as", "about", "from", "by",
    "on", "at", "in", "into", "through"
}

OLLAMA_API_URL = "http://localhost:11434/api/generate"
_OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"


def _probe_ollama_available(timeout: float = 0.10) -> bool:
    """
    Quick liveness check: GET /api/tags with a 100ms timeout.
    Returns True if Ollama is running and reachable, False otherwise.
    Called ONCE at module import so Tier 2 is skipped for the entire session
    when Ollama is not available (e.g. at college without a local GPU).
    """
    try:
        r = requests.get(_OLLAMA_TAGS_URL, timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


OLLAMA_AVAILABLE: bool = _probe_ollama_available()
if not OLLAMA_AVAILABLE:
    print(
        "[TurnClassifier] Ollama not reachable — Tier 2 LLM classification DISABLED. "
        "Tier 1 regex only; fallback defaults to COMPLETE (no 2.3s extension).",
        flush=True,
    )


def check_thought_completion(transcript: str) -> str:
    """
    Returns 'COMPLETE' or 'INCOMPLETE'.
    Uses Tier 1 (Regex) first. If uncertain, calls Tier 2 (Qwen2.5:1.5b).
    """
    if not transcript:
        return "INCOMPLETE"

    clean_text = transcript.strip().rstrip(".,!?")
    words = clean_text.lower().split()

    if not words:
        return "INCOMPLETE"

    last_word = words[-1]

    # --- TIER 1: FAST REGEX & LEXICAL RULES (0ms) ---
    # Case A: Explicit filler or trailing conjunction -> User is thinking
    if last_word in THINKING_FILLER_WORDS or transcript.strip().endswith("..."):
        return "INCOMPLETE"

    # Case B: Sentence ends with clear terminal punctuation in original transcript
    # Removed: Whisper STT automatically adds periods when the user pauses, 
    # even if the thought is incomplete. Relying on punctuation causes premature cutoffs.
    # if transcript.strip().endswith((".", "?", "!")) and len(words) >= 4:
    #     return "COMPLETE"

    # --- TIER 2: QWEN 2.5:1.5B PROBE (~100ms) ---
    # Skipped when OLLAMA_AVAILABLE is False (no local LLM running at this location).
    # Fallback returns COMPLETE in that case — safe choice when we can't classify;
    # avoids the blanket 2.3s pause extension that occurred when Ollama timed out.
    if not OLLAMA_AVAILABLE:
        return "COMPLETE"

    prompt = (
        "Task: Determine if the candidate's sentence is complete or interrupted mid-thought.\n"
        f'Transcript: "{clean_text}"\n'
        "Output ONLY one word: 'COMPLETE' or 'INCOMPLETE'."
    )

    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 3,
                    "temperature": 0.0,
                    "top_p": 0.1
                }
            },
            timeout=0.600  # 600ms safety timeout fallback
        )
        if response.status_code == 200:
            result = response.json().get("response", "").strip().upper()
            if "INCOMPLETE" in result:
                return "INCOMPLETE"
            return "COMPLETE"
    except Exception:
        # Fallback: Ollama WAS available at startup but timed out on this call.
        # Return COMPLETE (do not extend pause) — avoids stalling for 2.3s every turn
        # in environments where Ollama is slow or intermittently overloaded.
        return "COMPLETE"

    # Default fallback if uncertain
    return "COMPLETE"

if __name__ == "__main__":
    test_cases = [
        "I think we should use FastAPI because",
        "FastAPI is very fast and efficient.",
        "Well, um...",
        "The database handles connection pooling",
    ]
    print("Testing Turn Classifier...")
    for text in test_cases:
        res = check_thought_completion(text)
        print(f"'{text}' -> {res}")
