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


MODEL_NAME = "qwen2.5:3b"

EVA_CONVERSATIONAL_SYSTEM_PROMPT = """You are Eva, a warm, intelligent, and highly empathetic Senior Technical Interviewer.

PERSONALITY & VOICE RULES:
1. Speak in concise, natural spoken English (15-35 words max per response).
2. Use subtle conversational anchors like "Ah,", "Got it,", "Makes sense,", or "Fair point," to start responses naturally.
3. NEVER sound like a rigid script reader. Always connect your transition directly to what the candidate said.
4. If the candidate asks about you, your role, or the interview format, answer warmly in 1 short sentence before guiding them back.

OUTPUT FORMAT (STRICT):
<think>1 short sentence summarizing candidate tone, intent, or technical accuracy</think>
<speak>Your actual spoken words to the candidate</speak>
"""


class TextSanitizer:
    """
    Cleans LLM text output and injects subtle prosodic cues for Kokoro-82M TTS.
    """
    @staticmethod
    def clean_for_tts(text: str) -> str:
        if not text:
            return ""

        # 1. Strip residual XML tags
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'</?speak>', '', text)

        # 2. Preserve code inside backticks by removing ONLY the backtick symbols, NOT the code
        text = text.replace('`', '')
        text = text.replace('*', '').replace('#', '')

        # 3. Strip bracketed action descriptions like [Sighs] or (clears throat) without wiping out code params like (1)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\((?:sighs|clears throat|nods|laughs|pauses|chuckles|giggles)\)', '', text, flags=re.IGNORECASE)

        # 4. Inject prosodic comma pauses after common speech fillers
        fillers = ["Ah", "Hmm", "Got it", "Right", "Makes sense", "Fair point", "Sure", "Loud and clear", "Yes"]
        for filler in fillers:
            text = re.sub(rf'\b({filler})\b(?!\s*[,.!?:])', r'\1,', text, flags=re.IGNORECASE)

        # 5. Replace robotic written phrases with natural spoken equivalents
        text = re.sub(r"\bLet's move to your next question then\b", "Let's pivot to the next topic", text, flags=re.IGNORECASE)
        text = re.sub(r"\bNext question:\b", "Next up,", text, flags=re.IGNORECASE)

        # 6. Cleanup trailing whitespace & duplicate punctuation
        text = re.sub(r',\s*,', ',', text)
        return re.sub(r'\s+', ' ', text).strip()


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
    max_retries: int = 3,
    speaker_player=None,
    session_state=None
) -> Tuple[str, str]:
    """
    Returns (think_text, speak_text).
    Streams speak tokens directly to speaker_player as they arrive.

    :param conversation_history: List of message dicts tracking the interview.
    :param custom_system_prompt: Optional custom system prompt string or message dict.
    :param max_retries: Number of retry attempts on failure.
    :param speaker_player: Optional PersistentSpeaker instance to stream clauses to.
    :param session_state: Optional SessionState for the speaker.
    :return: A tuple containing (think_text, speak_text).
    """
    if custom_system_prompt:
        if isinstance(custom_system_prompt, str):
            sys_msg = {"role": "system", "content": custom_system_prompt}
        else:
            sys_msg = custom_system_prompt
    else:
        sys_msg = {"role": "system", "content": EVA_CONVERSATIONAL_SYSTEM_PROMPT}

    full_messages = [sys_msg] + conversation_history

    options = {
        "num_predict": 250,        # Accommodates <think> block + 35-word <speak> block
        "temperature": 0.7,        # Optimal balance of natural speech variation and instruction following
        "top_p": 0.9,
        "repeat_penalty": 1.15,    # Prevent "Great, let's move on..." loops
    }

    for attempt in range(max_retries):
        try:
            stream = ollama.chat(
                model=MODEL_NAME,
                messages=full_messages,
                stream=True,
                options=options
            )

            raw_output = ""
            clause_regex = re.compile(r'([,?!.\n])')
            in_speak_block = False
            speak_buffer = ""
            
            print("\n[Brain] Live LLM Output: ", end="", flush=True)
            for chunk in stream:
                token = chunk.get("message", {}).get("content", "")
                if token:
                    raw_output += token
                    print(token, end="", flush=True)
                    
                    if speaker_player and session_state:
                        if not in_speak_block:
                            speak_match = re.search(r'(?:<speak>|speak:|\[speak\]|peak>)(.*)', raw_output, flags=re.IGNORECASE | re.DOTALL)
                            if speak_match:
                                in_speak_block = True
                                token = speak_match.group(1)
                                
                        if in_speak_block:
                            clean_token = token
                            if "</speak>" in clean_token:
                                clean_token = clean_token.split("</speak>")[0]
                                in_speak_block = False
                                
                            speak_buffer += clean_token
                            
                            parts = clause_regex.split(speak_buffer)
                            if len(parts) > 1:
                                clause_to_speak = "".join(parts[:-1])
                                speak_buffer = parts[-1]
                                
                                if clause_to_speak.strip():
                                    speaker_player.speak_clause(clause_to_speak, session_state)

            print("\n") # Newline after streaming finishes
            
            think_text, speak_text = parse_think_speak(raw_output)
            
            if speaker_player and session_state:
                if in_speak_block and speak_buffer.strip():
                    speaker_player.speak_clause(speak_buffer, session_state)
                elif not in_speak_block and speak_text.strip() and speak_text != "Got it, let's continue.":
                    speaker_player.speak_clause(speak_text, session_state)
            
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