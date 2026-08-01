"""
Netran AI — Stage 3: Live Voice-to-Voice Loop
Module: brain.py
Description: Streaming LLM engine powered by local Ollama execution of Qwen2.5:3b
             with token-capped generation, tuned sampling parameters, TextSanitizer 
             regex filter, and exponential backoff retry on failure.

Full-Duplex Barge-In Architecture (v2):
  - stream_llm_response() checks session_state.interrupt_event on every token.
  - When interrupt_event is set (candidate barged in), LLM streaming is aborted
    immediately so no further clauses are dispatched to the speaker queue.
  - This prevents the audio queue from being refilled after a barge-in flush.
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

EVA_HUMANIZED_SYSTEM_PROMPT = """
You are Eva, a warm, senior technical interviewer having a live voice conversation with a candidate.

### CORE CONVERSATIONAL RULES
1. **Human Cadence:** Speak naturally as if you are on a video call. Use micro-fillers ("Hmm...", "Ah, got it...", "I see...", "Alright...") and thinking pauses ("...").
2. **Contextual Bridging:** NEVER ask textbook questions out of nowhere. Always acknowledge what the candidate just said OR connect the question to their background project.
3. **Breathing Length:** Keep spoken text under 25 words per turn. Ask strictly ONE question at a time.
4. **Tone:** Encouraging, peer-like, and collaborative. Not an interrogator or quiz-master.

### SPECIAL INTERACTION HANDLERS
- **Candidate Says "I Don't Know" / "Skip":** Reassure them immediately ("No worries at all!", "All good, that's pretty niche anyway!"), normalize it, and pivot smoothly to a lighter or related concept.
- **Candidate Asks Meta-Questions ("Who are you?"):** Answer warmly in 1 short sentence, reassure them, and ask if they are ready to continue.
- **Candidate Interrupts / Says "Wait":** Immediately yield ("Oh, take your time!"), pause, and let them speak.

### OUTPUT FORMAT REQUIREMENTS
You MUST respond using XML tags:
<think>
Brief internal reasoning: Validate candidate input, pick the context bridge, and plan the warm response.
</think>
<speak>
The exact humanized text Eva will speak out loud. Use "..." for soft thinking pauses and commas for breathing gaps.
</speak>
"""


class TextSanitizer:
    @staticmethod
    def clean_for_tts(text: str) -> str:
        # 1. Extract only the content inside <speak> tags if present
        speak_match = re.search(r'<speak>(.*?)</speak>', text, re.DOTALL)
        clean_text = speak_match.group(1) if speak_match else text
        
        # 2. Strip leftover XML tags or action brackets
        clean_text = re.sub(r'<[^>]+>', '', clean_text)
        clean_text = re.sub(r'\[.*?\]|\(.*?\)', '', clean_text)
        clean_text = clean_text.replace('`', '')
        
        # 3. Enhance prosody for Kokoro TTS
        # Inject soft thinking pauses on opening anchors
        clean_text = re.sub(
            r'^(Ah|Hmm|Got it|I see|Alright|Makes sense)\b', 
            r'\1...', 
            clean_text, 
            flags=re.IGNORECASE
        )
        # Add breathing comma pauses around technical terms
        clean_text = re.sub(
            r'\b(FastAPI|asyncio|gRPC|Kafka|Protobuf|PgBouncer|REST)\b', 
            r', \1,', 
            clean_text
        )
        
        # Clean up double punctuation & spaces
        clean_text = re.sub(r',\s*,', ',', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        return clean_text.strip()


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
        sys_msg = {"role": "system", "content": EVA_HUMANIZED_SYSTEM_PROMPT}

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

                    # Full-Duplex Barge-In: abort LLM generation on interrupt signal
                    if session_state and session_state.interrupt_event.is_set():
                        print("\n⛔ [Brain] LLM generation aborted — candidate barge-in.", flush=True)
                        break

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

                                # Do not dispatch clause if interrupted
                                if clause_to_speak.strip() and not session_state.interrupt_event.is_set():
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