"""
Turn Classifier Module (Case 3 Hybrid Architecture)
Determines whether candidate speech is a complete thought or an interrupted pause/thinking state.
Tier 1: Ultra-fast regex check (0ms).
Tier 2: Qwen2.5:1.5B classification via local Ollama API (~80-120ms fallback).
"""

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
    prompt = (
        "Task: Determine if the candidate's sentence is complete or interrupted mid-thought.\n"
        f'Transcript: "{clean_text}"\n'
        "Output ONLY one word: 'COMPLETE' or 'INCOMPLETE'."
    )

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "qwen2.5:1.5b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 3,
                    "temperature": 0.0,
                    "top_p": 0.1
                }
            },
            timeout=0.250  # 250ms safety timeout fallback
        )
        if response.status_code == 200:
            result = response.json().get("response", "").strip().upper()
            if "INCOMPLETE" in result:
                return "INCOMPLETE"
            return "COMPLETE"
    except Exception:
        # Fallback safety if 1.5B model is busy, not pulled, or times out
        return "INCOMPLETE"  # Safer to wait and give candidate more time

    # Default fallback if uncertain
    return "INCOMPLETE"

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
