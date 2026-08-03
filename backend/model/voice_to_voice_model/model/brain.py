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

import logging
import os
import re
import time

# Suppress HTTPX and HTTPCORE debug logs from flooding terminal output
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

import ollama

try:
    from .benchmark import Benchmark
    from .config import OLLAMA_MODEL
except ImportError:
    try:
        from model.voice_to_voice_model.model.benchmark import Benchmark
        from model.voice_to_voice_model.model.config import OLLAMA_MODEL
    except ImportError:
        OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        from benchmark import Benchmark

try:
    from .prompts import SYSTEM_PROMPT
except ImportError:
    try:
        from model.voice_to_voice_model.model.prompts import SYSTEM_PROMPT
    except ImportError:
        pass


MODEL_NAME = OLLAMA_MODEL

TONE_SPEED_MAP: dict[str, float] = {
    "empathetic": 0.92,
    "encouraging": 0.92,
    "curious": 1.05,
    "probing": 1.05,
    "direct": 1.00,
    "technical": 1.00,
    "warm": 0.96,
    "icebreaker": 0.96,
}


def get_speed_for_tone(tone: str | None, default_speed: float = 1.00) -> float:
    """
    Maps LLM tone attribute to Kokoro TTS synthesis speed factor with boundary clamping [0.88x, 1.08x].
    """
    if not tone:
        return default_speed
    tone_lower = tone.strip().lower()
    raw_speed = TONE_SPEED_MAP.get(tone_lower, default_speed)
    return max(0.88, min(1.08, float(raw_speed)))


EVA_HUMANIZED_SYSTEM_PROMPT = """
You are Eva, a warm, articulate, and natural lead technical interviewer having a live voice conversation with a candidate.

### CORE CONVERSATIONAL RULES
1. **Spoken Human Cadence:** Speak casually as if you are on a real-time voice call. Use natural contractions ("I'm", "it's", "let's", "that's") and short vocal anchors ("Ah, got it...", "Hmm, good point...", "Right...").
2. **Concise Spoken Turns:** Keep every spoken response short (1 to 2 sentences max, 15–25 words). Never output long written lists, multi-bullet points, or textbook lectures.
3. **Contextual Bridging:** NEVER ask isolated textbook questions out of nowhere. Always acknowledge what the candidate just said OR connect the question to their background project.
4. **Structural Spoken Template:** Structure every spoken response in 3 micro-phases:
   - **Vocal Anchor (1–3 words):** Start with natural opening feedback ("Ah, got it...", "Hmm, good point...", "Right...").
   - **Core Answer / Follow-up (15–25 words):** Provide concise feedback or context in 1 to 2 complete sentences.
   - **Terminal Question (5–10 words):** Ask a direct, clear question handing the conversation back to the candidate.
5. **Tone Selection:** Encouraging, peer-like, and collaborative. Select an appropriate tone attribute from the Tone Taxonomy below.

### TONE TAXONOMY
Choose ONE tone attribute for the TONE: line matching the candidate's turn context:
- `empathetic` / `encouraging`: Candidate hesitates, stumbles, says "I don't know" or "skip", or gives a weak answer.
- `curious` / `probing`: Candidate gives a strong answer; escalating to trade-offs, architecture, or edge cases.
- `direct` / `technical`: Baseline introduction of a new technical topic or standard baseline question.
- `warm` / `icebreaker`: Candidate introduction phase or casual conversational meta-questions ("Who created you?").

### SPECIAL INTERACTION HANDLERS
- **Candidate Says "I Don't Know" / "Skip":** Reassure them immediately ("No worries at all!", "All good, that's pretty niche anyway!"), normalize it, and pivot smoothly to a lighter concept.
- **Candidate Asks Meta-Questions ("Who are you?"):** Answer warmly in 1 short sentence, reassure them, and ask if they are ready to continue.
- **Candidate Interrupts / Says "Wait":** Immediately yield ("Oh, take your time!"), pause, and let them speak.

### OUTPUT FORMAT REQUIREMENTS & STRICT DIRECTIVES
1. **Spoken Response Format:** You MUST respond in EXACTLY two lines. Do NOT include any thinking, reasoning, or XML tags.
2. **Line 1 (TONE):** Start with "TONE: " followed by ONE tone attribute from the Tone Taxonomy (e.g., "TONE: empathetic").
3. **Line 2 (SPEAK):** Start with "SPEAK: " followed by your 15-25 word response.
4. **MANDATORY CALL-TO-ACTION (CTA) HANDOFF:** Every SPEAK payload MUST end with a terminal question mark (?) or an explicit turn handoff question. NEVER end a turn with a passive statement.
"""


class TextSanitizer:
    @staticmethod
    def clean_for_tts(text: str, tone: str = "direct") -> str:
        if not text:
            return ""

        clean_text = text
        
        # Strip leftover XML tags or action brackets just in case
        clean_text = re.sub(r'<[^>]+>', '', clean_text)
        clean_text = re.sub(r'\[.*?\]|\(.*?\)', '', clean_text)
        clean_text = clean_text.replace('`', '')
        
        # Strip any leaked TONE: or SPEAK: artifacts
        clean_text = re.sub(r'TONE:\s*\w+', '', clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r'SPEAK:\s*', '', clean_text, flags=re.IGNORECASE)
        
        # 3. Tone-Specific Micro-Prosody & Conversational Anchors
        tone_lower = tone.strip().lower() if tone else "direct"

        if tone_lower in ("empathetic", "encouraging"):
            # Soft opening ellipses & reassuring pauses
            clean_text = re.sub(
                r'^(Ah|No worries|All good|Don\'t worry|Hmm|Got it|I see)\b',
                r'\1...',
                clean_text,
                flags=re.IGNORECASE
            )
        elif tone_lower in ("warm", "icebreaker"):
            # Natural breathing commas & friendly anchors
            clean_text = re.sub(
                r'^(Hey there|Well|Hi|Hello|Ah|Right)\b',
                r'\1,',
                clean_text,
                flags=re.IGNORECASE
            )
        else:
            # Inject soft thinking pauses on standard vocal anchors
            clean_text = re.sub(
                r'^(Ah|Hmm|Got it|I see|Alright|Makes sense)\b',
                r'\1...',
                clean_text,
                flags=re.IGNORECASE
            )

        # 4. Forced Technical Micro-Pauses (em-dashes around technical jargon)
        clean_text = re.sub(
            r'\b(FastAPI|asyncio|gRPC|Kafka|Protobuf|PgBouncer|PostgreSQL|REST|Docker|Kubernetes)\b\s+with\b',
            r'\1--with',
            clean_text,
            flags=re.IGNORECASE
        )
        clean_text = re.sub(
            r'\b(FastAPI|asyncio|gRPC|Kafka|Protobuf|PgBouncer|REST)\b',
            r', \1,',
            clean_text,
            flags=re.IGNORECASE
        )

        # 5. Kokoro TTS Prosody Fix: Replace Exclamation Marks with Soft Periods to Eliminate Pitch Spikes
        clean_text = clean_text.replace("!", ".")

        # Clean up double punctuation & multi-spaces
        clean_text = re.sub(r',\s*,', ',', clean_text)
        clean_text = re.sub(r'--\s*--', '--', clean_text)
        clean_text = re.sub(r'\.\s*\.', '.', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        return clean_text.strip()


def stream_llm_response(
    conversation_history: list[dict[str, str]],
    custom_system_prompt: str | dict[str, str] | None = None,
    max_retries: int = 3,
    speaker_player=None,
    session_state=None,
    ui_callback=None
) -> tuple[str, str]:
    """
    Returns (think_text, speak_text).
    Streams speak tokens directly to speaker_player as they arrive.

    :param conversation_history: List of message dicts tracking the interview.
    :param custom_system_prompt: Optional custom system prompt string or message dict.
    :param max_retries: Number of retry attempts on failure.
    :param speaker_player: Optional PersistentSpeaker instance to stream clauses to.
    :param session_state: Optional SessionState for the speaker.
    :param ui_callback: Optional callback to stream UI updates (event_type, content).
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
        "num_predict": 380,        # Refined headroom to prevent truncation mid-sentence
        "temperature": 0.65,       # Tuned for consistent CTA formatting & closing punctuation
        "top_p": 0.85,             # High-probability token selection for grammatical endings
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
            line_buffer = ""
            in_speak_mode = False
            full_speak_text = ""
            speak_buffer = ""
            detected_tone = "direct"
            first_token_received = False

            print("\n[Brain] Live LLM Output: ", end="", flush=True)
            for chunk in stream:
                token = chunk.get("message", {}).get("content", "")
                if token:
                    if not first_token_received:
                        if Benchmark.get_start_time("ttft"):
                            ttft_ms = Benchmark.end("ttft")
                            Benchmark.last_ttft_ms = ttft_ms
                            print(f"[Benchmark] Time-To-First-Token (TTFT): {ttft_ms:.1f}ms", flush=True)
                        first_token_received = True

                    raw_output += token
                    print(token, end="", flush=True)

                    # Full-Duplex Barge-In: abort LLM generation on interrupt signal
                    if session_state and session_state.interrupt_event.is_set():
                        print("\n⛔ [Brain] LLM generation aborted — candidate barge-in.", flush=True)
                        break

                    if not in_speak_mode:
                        line_buffer += token
                        
                        has_newline = "\n" in line_buffer
                        has_speak = "SPEAK:" in line_buffer.upper()
                        too_long = len(line_buffer) > 60
                        
                        ready_to_speak = False
                        if has_speak or too_long:
                            ready_to_speak = True
                        elif has_newline:
                            # If there is text after a newline, assume the LLM forgot SPEAK:
                            parts = line_buffer.split("\n", 1)
                            if len(parts) > 1:
                                after_newline = parts[1].lstrip()
                                if len(after_newline) > 0 and not "SPEAK:".startswith(after_newline.upper()):
                                    ready_to_speak = True
                        
                        if ready_to_speak:
                            # 1. Parse TONE line
                            tone_match = re.search(r"TONE:\s*([a-zA-Z_]+)", line_buffer, re.IGNORECASE)
                            if tone_match:
                                detected_tone = tone_match.group(1).lower()
                                if session_state:
                                    session_state.current_tone = detected_tone
                                    session_state.tts_speed = get_speed_for_tone(detected_tone)

                            # 2. Transition to speak mode
                            in_speak_mode = True
                            if ui_callback:
                                ui_callback("speak_start", "")

                            # 3. Clean buffer and extract initial spoken text
                            clean_buf = re.sub(r"TONE:\s*[a-zA-Z_]+\s*\n?", "", line_buffer, flags=re.IGNORECASE)
                            clean_buf = re.sub(r"SPEAK:\s*", "", clean_buf, flags=re.IGNORECASE)
                            initial_text = clean_buf.lstrip()
                            
                            if initial_text:
                                full_speak_text += initial_text
                                if ui_callback:
                                    ui_callback("speak_chunk", initial_text)
                                speak_buffer += initial_text
                                # Process initial clause if any
                                parts = clause_regex.split(speak_buffer)
                                if len(parts) > 1:
                                    clause_to_speak = "".join(parts[:-1])
                                    speak_buffer = parts[-1]
                                    if speaker_player and session_state and clause_to_speak.strip() and not session_state.interrupt_event.is_set():
                                        speaker_player.speak_clause(clause_to_speak, session_state, tone=detected_tone)
                    else:
                        full_speak_text += token
                        if ui_callback:
                            ui_callback("speak_chunk", token)

                        speak_buffer += token
                        parts = clause_regex.split(speak_buffer)
                        if len(parts) > 1:
                            clause_to_speak = "".join(parts[:-1])
                            speak_buffer = parts[-1]

                            # Do not dispatch clause if interrupted
                            if speaker_player and session_state and clause_to_speak.strip() and not session_state.interrupt_event.is_set():
                                speaker_player.speak_clause(clause_to_speak, session_state, tone=detected_tone)

            print("\n") # Newline after streaming finishes
            
            # Flush remaining buffer
            if speaker_player and session_state and speak_buffer.strip() and not session_state.interrupt_event.is_set():
                speaker_player.speak_clause(speak_buffer.strip(), session_state, tone=detected_tone)

            clean_speak_text = TextSanitizer.clean_for_tts(full_speak_text)
            
            # Software Guardrail Safety Net: Enforce terminal punctuation handoff
            if clean_speak_text and not clean_speak_text.endswith(('?', '.', '!')):
                clean_speak_text = clean_speak_text + "... What are your thoughts on that?"
                if speaker_player and session_state and not session_state.interrupt_event.is_set():
                     speaker_player.speak_clause("... What are your thoughts on that?", session_state, tone=detected_tone)

            if session_state:
                session_state.current_tone = detected_tone
                session_state.tts_speed = get_speed_for_tone(detected_tone)
            
            return "", clean_speak_text

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


def preload(custom_system_prompt: str | None = None):
    """Preloads the Ollama LLM engine into memory to ensure instant first response."""
    print("Pre-heating Ollama LLM engine...", flush=True)
    try:
        # stream_llm_response() returns a tuple ("", speak_text), NOT a generator.
        # Calling it directly (with no speaker_player) warms up the Ollama model without
        # dispatching any audio or modifying conversation state.
        stream_llm_response(
            [{"role": "user", "content": "."}],
            custom_system_prompt=custom_system_prompt
        )
    except Exception:
        pass

if __name__ == "__main__":
    print("Testing Brain Module & TextSanitizer...")
    sample_text = "[Clears Throat] *Nods encouragingly* (Sighs) **Understood.** Let us move to FastAPI."
    cleaned = TextSanitizer.clean_for_tts(sample_text)
    print("Raw Text:", sample_text)
    print("Cleaned for TTS:", cleaned)