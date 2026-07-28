"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: brain.py
Description: Streaming LLM engine powered by local Ollama execution of Qwen2.5:1.5b
             with TextSanitizer regex filter to strip non-speech roleplay tokens.
"""

import re
from typing import Dict, List, Optional, Union
import ollama

try:
    from .prompts import SYSTEM_PROMPT
except ImportError:
    try:
        from model.voice_to_voice_model.model.prompts import SYSTEM_PROMPT
    except ImportError:
        from prompts import SYSTEM_PROMPT


class TextSanitizer:
    """
    Sanitizes LLM response text by stripping non-speech roleplay tags,
    bracketed expressions, and markdown symbols before feeding into TTS.
    """
    @staticmethod
    def clean_for_tts(text: str) -> str:
        if not text:
            return ""
        # Strips bracketed text like [Clears Throat], (Sighs)
        cleaned = re.sub(r'\[.*?\]|\(.*?\)', '', text)
        # Strips markdown symbols like *action*, **bold**
        cleaned = re.sub(r'\*+', '', cleaned)
        # Normalizes extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned


def generate_eva_response(
    conversation_history: List[Dict[str, str]],
    custom_system_prompt: Optional[Union[str, Dict[str, str]]] = None
):
    """
    Sends the ongoing conversation history to Ollama (Qwen2.5)
    and yields tokens in real time.

    :param conversation_history: List of message dicts tracking the interview.
    :param custom_system_prompt: Optional custom system prompt string or message dict.
    :return: A generator yielding text chunks as they arrive from the model.
    """
    if custom_system_prompt:
        if isinstance(custom_system_prompt, str):
            sys_msg = {"role": "system", "content": custom_system_prompt}
        else:
            sys_msg = custom_system_prompt
    else:
        sys_msg = SYSTEM_PROMPT

    full_messages = [sys_msg] + conversation_history

    try:
        stream = ollama.chat(
            model="qwen2.5:1.5b",
            messages=full_messages,
            stream=True
        )

        for chunk in stream:
            token = chunk.get("message", {}).get("content", "")
            if token:
                yield token

    except Exception as e:
        yield f"\n[Brain Error: Make sure Ollama is running and qwen2.5 is pulled. Details: {e!s}]"


def preload(custom_system_prompt: Optional[str] = None):
    """Preloads the Ollama LLM engine into memory to ensure instant first response."""
    print("Pre-heating Ollama LLM engine...", flush=True)
    try:
        for _ in generate_eva_response([{"role": "user", "content": "."}], custom_system_prompt=custom_system_prompt):
            pass
    except Exception:
        pass


if __name__ == "__main__":
    print("Testing Brain Module & TextSanitizer...")
    sample_text = "[Clears Throat] *Nods encouragingly* (Sighs) **Understood.** Let us move to FastAPI."
    cleaned = TextSanitizer.clean_for_tts(sample_text)
    print("Raw Text:", sample_text)
    print("Cleaned for TTS:", cleaned)