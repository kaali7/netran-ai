"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: brain.py
Description: Streaming LLM engine powered by local Ollama execution of Qwen2.5:1.5b
             with token-capped generation, tuned sampling parameters, TextSanitizer 
             regex filter, and exponential backoff retry on failure.
"""

import re
import time
from typing import Dict, Generator, List, Optional, Union, Tuple

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
        cleaned = re.sub(r'\[.*?\]|\(.*?\)', '', text)
        cleaned = re.sub(r'\*+', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned


def parse_think_speak(raw: str) -> Tuple[str, str]:
    """
    Splits LLM raw output into (think_text, speak_text).
    Uses fuzzy matching and positional inference to handle heavily malformed LLM outputs.
    """
    raw = raw.strip()
    think_text = ""
    speak_text = ""
    
    # 1. Fuzzy match speak tag (catches <speak>, speak:, [speak], and typos like peak>)
    speak_pattern = r'(?:<speak>|speak:|\[speak\]|peak>)(.*?)(?:</speak>|$)'
    speak_match = re.search(speak_pattern, raw, re.DOTALL | re.IGNORECASE)
    
    # 2. Fuzzy match think tag
    think_pattern = r'(?:<think>|think:|\[think\])(.*?)(?:</think>|<speak>|speak:|\[speak\]|peak>|$)'
    think_match = re.search(think_pattern, raw, re.DOTALL | re.IGNORECASE)
    
    if think_match:
        think_text = think_match.group(1).strip()
    if speak_match:
        speak_text = speak_match.group(1).strip()
        
    # 3. Positional Inference (The Safety Net)
    if speak_text and not think_text:
        # Everything before the speak tag is reasoning
        parts = re.split(r'(?:<speak>|speak:|\[speak\]|peak>)', raw, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) > 1:
            think_text = re.sub(r'^(?:<think>|think:|\[think\])', '', parts[0], flags=re.IGNORECASE).strip()
            
    elif think_text and not speak_text:
        # Everything outside the think tag is speech
        parts = re.split(r'</think>', raw, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) > 1:
            speak_text = parts[1].strip()
        else:
            # If no closing tag, try paragraphs
            parts = re.split(r'\n\s*\n', think_text)
            if len(parts) > 1:
                speak_text = parts[-1].strip()
                think_text = "\n\n".join(parts[:-1]).strip()

    # 4. Paragraph Inference (Complete failure of tags)
    if not think_text and not speak_text:
        parts = re.split(r'\n\s*\n', raw)
        if len(parts) > 1:
            speak_text = parts[-1].strip()
            think_text = "\n\n".join(parts[:-1]).strip()
        else:
            speak_text = raw

    # Cleanup and fallback
    speak_text = re.sub(r'^(?:speak:\s*)', '', speak_text, flags=re.IGNORECASE).strip()
    if not speak_text:
        speak_text = "Got it, let's continue."
        
    return think_text, speak_text


def stream_llm_response(
    conversation_history: List[Dict[str, str]],
    custom_system_prompt: Optional[Union[str, Dict[str, str]]] = None,
    max_retries: int = 3
) -> Tuple[str, str]:
    """
    Returns (think_text, speak_text) — no longer a streaming generator.
    Buffers full LLM output first, then parses think/speak tags.

    :param conversation_history: List of message dicts tracking the interview.
    :param custom_system_prompt: Optional custom system prompt string or message dict.
    :param max_retries: Number of retry attempts on failure.
    :return: A tuple containing (think_text, speak_text).
    """
    if custom_system_prompt:
        if isinstance(custom_system_prompt, str):
            sys_msg = {"role": "system", "content": custom_system_prompt}
        else:
            sys_msg = custom_system_prompt
    else:
        sys_msg = SYSTEM_PROMPT

    full_messages = [sys_msg] + conversation_history

    options = {
        "num_predict": 512,        # Extended for <think> and <speak> blocks
        "temperature": 0.7,        # ISSUE-7: Natural phrasing variation
        "top_p": 0.9,
        "repeat_penalty": 1.15,    # Prevent "Great, let's move on..." loops
    }

    for attempt in range(max_retries):
        try:
            stream = ollama.chat(
                model="qwen2.5:1.5b",
                messages=full_messages,
                stream=True,
                options=options
            )

            raw_output = ""
            print("\n[Brain] Live LLM Output: ", end="", flush=True)
            for chunk in stream:
                token = chunk.get("message", {}).get("content", "")
                if token:
                    raw_output += token
                    print(token, end="", flush=True)

            print("\n") # Newline after streaming finishes
            
            think_text, speak_text = parse_think_speak(raw_output)
            print(f"[Brain] Extracted THINK: {repr(think_text[:100])}...")
            print(f"[Brain] Extracted SPEAK: {repr(speak_text[:100])}...\n", flush=True)
            return think_text, speak_text

        except Exception as e:
            if attempt < max_retries - 1:
                wait_sec = 0.5 * (2 ** attempt)
                print(f"[Brain] Retry {attempt + 1}/{max_retries} after {wait_sec}s: {e}", flush=True)
                time.sleep(wait_sec)
            else:
                print(f"[Brain] All retries exhausted: {e}", flush=True)
                return ("", "I apologize, let's move forward to the next question.")


# Backward-compatible alias for existing front.py references
generate_eva_response = stream_llm_response


def preload(custom_system_prompt: Optional[str] = None):
    """Preloads the Ollama LLM engine into memory to ensure instant first response."""
    print("Pre-heating Ollama LLM engine...", flush=True)
    try:
        for _ in stream_llm_response(
            [{"role": "user", "content": "."}],
            custom_system_prompt=custom_system_prompt
        ):
            pass
    except Exception:
        pass

if __name__ == "__main__":
    print("Testing Brain Module & TextSanitizer...")
    sample_text = "[Clears Throat] *Nods encouragingly* (Sighs) **Understood.** Let us move to FastAPI."
    cleaned = TextSanitizer.clean_for_tts(sample_text)
    print("Raw Text:", sample_text)
    print("Cleaned for TTS:", cleaned)