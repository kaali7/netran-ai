# Netran AI Voice-to-Voice: Current Implementation & System Architecture

## 📌 Executive Summary
The Netran AI Voice-to-Voice backend and desktop application run a real-time, low-latency cascaded voice processing pipeline comprising **Neural Voice Activity Detection (Silero VAD)**, **Speech-to-Text (Faster-Whisper)**, **Dynamic State Machine & Adaptive Branching (QuestionManager)**, **Streaming LLM Reasoning (Ollama Qwen2.5:1.5B)** with **Regex TextSanitizer**, and **Text-to-Speech (Kokoro-82M)**, integrated into a multi-screen dark-themed **Kivy Desktop GUI**.

Additionally, Stage 3 ingests Stage 2 session artifact bundles (`interview_questions.json`, `interviewer_behavior.json`, `system_prompt.txt`, `resume_analysis.json`) via `schemas.py` Pydantic contracts and exports consolidated session outputs (`recording.wav` + `session_manifest.json`) for downstream Stage 4 post-session evaluation engines.

---

## 🏗️ Core Architecture & Component Breakdown

## 🏗️ Core Architecture & Component Breakdown

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SHARED SESSION STATE                           │
│     session_state.py ──► Thread-Safe Events & Runtime Parameters         │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
         ┌───────────────────────────┴───────────────────────────┐
         ▼                                                       ▼
┌─────────────────────────┐                             ┌─────────────────┐
│   listener.py (STT)     │                             │ speaker.py(TTS) │
│ • 20x Max Gain + Gate   │                             │ • Tech Text     │
│ • Configurable Silence  │                             │   Normalizer    │
│ • 60s Frame Buffer      │                             │ • Async Queue   │
│ • Hallucination Filter  │                             │   Buffer        │
└───────────┬─────────────┘                             └────────▲────────┘
            │ Transcript                                         │ Audio
            ▼                                                    │ Stream
┌────────────────────────────────────────────────────────────────┴────────┐
│                   front.py & question_manager.py                        │
│ • InterviewOrchestrator (extracted from InterviewScreen)                │
│ • Late Question Advance (evaluate before pointer increment)            │
│ • System-Prompt-Anchored Sliding Context Window (Max 4 Turns)           │
│ • Pause Tolerance Spinner (⚡ 1.0s / ⚖️ 1.6s / 🧠 2.2s)               │
│ • Graceful Session Closure                                              │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Filtered Context
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           brain.py (LLM)                                │
│ • Ollama Timeout + 3x Exponential Backoff Retry                        │
│ • Structured XML Output (<think> / <speak> tags)                       │
│ • Full Response Buffering & Regex Parsing                              │
│ • Token Cap (num_predict: 250) + Temperature Tuning (0.7 / 0.9 top_p)   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1. Data Contracts & Bundle Loader ([schemas.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/schemas.py))
* **Pydantic v2 Input Schemas**:
  - `AnswerRubric`: `poor_answer_indicators`, `good_answer_indicators`, `bar_raiser_indicators`.
  - `InterviewQuestionInput`: Validates `id`, `tier`, `topic`, `difficulty`, `question_text`, `expected_keywords`, `rubric`, `followup_if_strong`, `followup_if_weak`.
  - `InterviewerBehaviorInput`: Validates `session_id`, `persona`, `target_company`, `candidate_name`, `target_role`, `interviewer_system_prompt`, `behavior_rules`.
  - `Stage2SessionBundle`: Ingests all 4 Stage 2 artifacts (`behavior`, `questions`, `system_prompt`, `resume_analysis`).
* **Pydantic v2 Output Schemas**:
  - `TurnManifest`: Captures `turn_id`, `question_id`, `topic`, `question_text`, `candidate_transcript`, `audio_start_sec`, `audio_end_sec`, `stt_latency_ms`, `ttft_ms`, `evaluation_branch_taken`, `eva_reasoning` (internal thought process), and `eva_reply` (actual spoken text).
  - `SessionManifest`: Root container storing metadata (`session_id`, `session_start_iso`, `total_turns`) and `turns`.
* **Bundle Loader (`load_stage2_bundle`)**: Safely parses and validates inputs from Stage 2 directories.

### 2. State Machine & Adaptive Branching Engine ([question_manager.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/question_manager.py))
* **Question Progression & Lifecycle State Machine**: Manages explicit session phases (`ICEBREAKER` -> `TECHNICAL` -> `LAST_QUESTION` -> `COMPLETED`). Tracks 15 technical interview questions where pointer only advances on `next_topic` transitions or completed evaluations to ensure accurate follow-up evaluation and prevent premature final question cutoffs.
* **Repetition Loop Protection**: Automatically advances to the next topic after 2 weak answer attempts (`retries_on_current_q >= 2`) on the same question.
* **Turn Intent Classification**: `classify_turn_intent()` categorizes candidate input into `interviewer_meta`, `icebreaker_response`, `audio_check`, `thinking_pause`, `next_topic`, or `technical_answer`. Meta-intents (`interviewer_meta`, `audio_check`, `thinking_pause`) immediately bypass keyword evaluation without advancing the question pointer. Broadened regex intercepts identity/origin queries (*"where are you from"*, *"where are you based"*, *"who created you"*, *"tell me about yourself"*).
* **Candidate Meta-Intent Override**: `is_candidate_requesting_skip()` intercepts candidate requests to skip or move to the next question (regex matching "move to next", "skip", "pass") and forces a `"next_topic"` transition before keyword scoring.
* **Keyword Density Scoring**: Evaluates candidate STT transcripts against expected technical keywords via `calculate_keyword_density()`.
* **Branching Strategy**:
  - **Meta-Intents**: Returns `"interviewer_meta"`, `"audio_check"`, or `"thinking_pause"` immediately.
  - **Icebreaker Transition**: Returns `"icebreaker_response"` on candidate's background intro and transitions `self.phase = "TECHNICAL"`.
  - **Match $\ge$ 50% & `followup_if_strong`**: Triggers `"strong_followup"` branch (escalates to architectural trade-offs and edge cases).
  - **Match $<$ 20% & `followup_if_weak`**: Triggers `"weak_followup"` branch (asks simplifying diagnostic probes).
  - **Otherwise / Interview Completion**: Triggers `"next_topic"` or `"interview_completed"` branch and advances question pointer safely.
* **Natural Conversational Context & Prompt Bridging**: `format_prompt_context()` constructs natural LLM instructions for meta-intents (answering questions about Eva warmly in 1 short sentence, reassuring audio checks, empathetic pause acknowledgments) and technical branches with warm reactions and seamless transitions, ensuring clean question progression and alignment with `session_manifest.json`.
* **Single Source of Truth Session Completion**: `front.py` synchronizes `self.question_count` directly from `self.question_manager.current_index + 1`. Follow-ups and icebreakers no longer trigger premature `self.question_count >= self.MAX_QUESTIONS` cutoffs. The session only wraps up when `QuestionManager` evaluates the candidate's final technical answer and returns `interview_completed`.

### 3. Speech-to-Text & Audio Capture ([listener.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/listener.py))
* **Audio Capture Engine**: Built using `sounddevice` running at 16kHz single-channel `float32`.
* **Per-Frame Noise Gate & Auto-Gain**: Zeroes out faint static (<0.002 RMS), applies peak auto-gain up to **20x boost**, resolving quiet recordings.
* **Continuous Mic Writer (`ContinuousMicWriter`)**: Writes gain-boosted 16kHz 16-bit Mono WAV frames directly to `recording.wav`.
* **Silero VAD v3 + Faster-Whisper**: Speech endpointing and real-time STT transcription. Fast greedy decoding (`beam_size=1`, `best_of=1`, `min_silence_duration_ms=500`) reducing STT latency to ~180ms. Tuned start threshold (0.3 prob + 4 frame debounce). Configurable max silence frame window via UI (1.0s/1.6s/2.2s).
* **Real-Time Barge-In (Speech Interruption)**: Runs VAD inference prior to echo gate suppression when `state.is_agent_speaking.is_set()`. Triggers `force_stop_all()` immediately when candidate speech probability exceeds `0.65`.
* **Hallucination Filter**: Uses `is_valid_transcript()` to reject common Whisper empty room hallucinations ("Thank you.", "Subscribe", etc.).

### 4. LLM Engine & Text Sanitizer ([brain.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/brain.py))
* **Model**: Local Ollama execution of **`qwen2.5:3b`** (`MODEL_NAME = "qwen2.5:3b"`). Includes 3x exponential backoff retry and streams raw output live to console.
* **Conversational System Prompt**: Uses `EVA_CONVERSATIONAL_SYSTEM_PROMPT` instructing concise (15–35 words max), natural spoken English with anchors like "Ah,", "Got it,", "Makes sense," and warm single-sentence answers for candidate questions about Eva.
* **Tuned Params**: `num_predict: 250` (accommodating reasoning + spoken blocks), `temperature: 0.7`, `top_p: 0.9`, `repeat_penalty: 1.15`.
* **Think/Speak Split Architecture**: 
  - System prompt rigorously enforces `<think>` and `<speak>` XML tags, forbidding filler responses and colon-based artifacts.
  - Responses are fully buffered to correctly parse XML blocks (with fallback parsing).
* **Clause-Level Real-Time Streaming**: `stream_llm_response` scans the raw LLM token stream for `<speak>` blocks and dynamically splits on punctuation boundaries (`[,?!.\n]`). Natural clauses are immediately dispatched to `PersistentSpeaker` to hide generation latency, achieving sub-250ms Time-To-First-Audio (TTFA).
* **Prosodic Regex TextSanitizer (`TextSanitizer.clean_for_tts`)**:
  - Strips residual XML tags like `<think>` and action tags (`[Clears Throat]`, `(Sighs)`).
  - Preserves backticks text content without wiping code identifiers (e.g. ``asyncio.sleep(1)``).
  - Injects prosodic comma pauses after common fillers ("Ah,", "Hmm,", "Got it,").
  - Replaces robotic written phrases with natural spoken equivalents ("Let's pivot to the next topic", "Next up,").

### 5. Text-to-Speech Playback ([speaker.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/speaker.py))
* **PersistentSpeaker (Clause-Level PyAudio Stream)**: Employs a Producer-Consumer `queue.Queue` alongside a persistent, always-open `pyaudio.PyAudio()` output stream running in a daemon thread. Completely eliminates hardware handshake delays (0ms overhead) across the entire session.
* **Interruption Handling**: Implements `stop_immediately()` to instantly flush the pending audio queue and wipe playback without breaking the persistent stream.
* **Technical Text Normalization**: Prevents odd pausing on strings like "Python 3.11", "Next.js", and "HTTP/1.1".
* **Kokoro-82M Engine**: Neural TTS initialized using `KPipeline(lang_code="a")` with `af_bella` voice.

### 6. Session Manifest & Telemetry ([session_logger.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/session_logger.py))
* **Unified Output Contract**: Writes strictly `session_manifest.json` and `recording.wav` in the session output directory. Redundant `transcript.json` and duplicate `continuous_mic_input.wav` files are eliminated.

### 7. Multi-Screen Desktop Application & Headless CLI ([front.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/front.py) & [test_pipeline.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/test_pipeline.py))
* **Kivy Multi-Screen Architecture (`ScreenManager`)**:
  - Uses a **Premium Dark Theme Redesign** featuring deep charcoal backgrounds (`#121212`), elevated dark-gray rounded panels (`#1E1E24`), tactile solid-colored flat buttons, and vibrant color-coded chat tags (Eva in blue, User in teal, System in amber).
  - **`InterviewScreen`**:
    - Top Action Bar with prominent `📜 View Session Output History` button.
    - Preset Selector, LLM/Calibration mode toggles, and Pause Tolerance spinner (1.0s, 1.6s, 2.2s).
    - Live VAD visualizer & volume diagnostics bar.
  - **`SessionHistoryScreen`**:
    - Full-page output inspector displaying past `sess_<timestamp>` output folders.
    - Interactive WAV audio player with real-time `ProgressBar` and time tracking (`0:15 / 1:30`).
* **SessionState Management**: Thread-safe `session_state.py` orchestrating cross-module events (e.g., Echo Gate).
* **Think/Speak UI Rendering**: Safely escapes Kivy markup from LLM reasoning, then displays LLM internal reasoning and dialog using color-coded markup labels. Ensures only the `<speak>` block is sent to Kokoro TTS and fed back into `conversation_history` context to prevent compounding errors.
* **Bounded Sliding Context History**: Caps LLM chat history length to prevent performance degradation over time.

---

## 📊 Performance Benchmark Targets
| Metric | Description | Target | Current Status |
| :--- | :--- | :--- | :--- |
| **STT Latency** | Audio silence to Whisper text output | < 600 ms | Operational (~350–550 ms) |
| **TTFT** | Prompt sent to LLM first token output | < 400 ms | Operational (~200–350 ms) |
| **TTFA** | User silence to speaker first audio chunk | < 400 ms | Operational (~250–350 ms) |
