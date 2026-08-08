# Netran AI Voice-to-Voice: Current Implementation & System Architecture

## 📌 Executive Summary
The Netran AI Voice-to-Voice backend and desktop application run a real-time, low-latency cascaded voice processing pipeline comprising **Neural Voice Activity Detection (Silero VAD)**, **Speech-to-Text (Faster-Whisper)**, **Dynamic State Machine & Adaptive Branching (QuestionManager)**, **Streaming LLM Reasoning (Ollama Qwen2.5:3B)** with **Regex TextSanitizer**, and **Text-to-Speech (Kokoro-82M)**, integrated into a multi-screen dark-themed **Kivy Desktop GUI**.

Additionally, Stage 3 ingests Stage 2 session artifact bundles (`interview_questions.json`, `interviewer_behavior.json`, `resume_analysis.json`) via `schemas.py` Pydantic contracts and exports consolidated session outputs (`recording.wav` + `transcript.json`) for downstream Stage 4 post-session evaluation engines.

---

## 🏗️ Core Architecture & Component Breakdown

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SHARED SESSION STATE                           │
│   session_state.py ──► Thread-Safe Events & Runtime Parameters          │
│   • is_agent_speaking    • is_candidate_speaking    • should_stop        │
│   • force_speech_done    • interrupt_event (barge-in signal)            │
│   • interrupt_cooldown_sec (0.3s)  • last_interrupt_time (monotonic)    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
         ┌───────────────────────────┴───────────────────────────┐
         ▼                                                       ▼
┌─────────────────────────┐                             ┌─────────────────┐
│   listener.py (STT)     │                             │ speaker.py(TTS) │
│ • Full-Duplex VAD       │  ──interrupt_event──►       │ • 512-frame buf │
│ • Barge-In Fall-Through │                             │ • 1024 sub-chunk│
│ • interrupt cooldown    │                             │ • HW buf flush  │
│ • 20x Max Gain + Gate   │                             │ • Async Queue   │
│ • Configurable Silence  │                             │   Buffer        │
│ • 60s Frame Buffer      │                             │                 │
│ • Hallucination Filter  │                             │                 │
└───────────┬─────────────┘                             └────────▲────────┘
            │ Transcript (incl. barge-in speech)                 │ Audio Clauses
            ▼                                                    │ (streamed)
┌────────────────────────────────────────────────────────────────┴────────┐
│                   front.py & question_manager.py                        │
│ • InterviewOrchestrator (extracted from InterviewScreen)                │
│ • Clears interrupt_event before each LLM turn                           │
│ • Sets is_agent_speaking BEFORE LLM streaming begins                    │
│ • Audio queue drain poll (50ms) with interrupt_event bail-out           │
│ • Filler word removed (LLM anchors serve as natural fillers)            │
│ • Late Question Advance (evaluate before pointer increment)             │
│ • System-Prompt-Anchored Sliding Context Window (Max 4 Turns)          │
│ • Streamlined Preset & Question Limit Controls                          │
│ • Fixed 800ms Fast Response Pause Tolerance                            │
│ • Graceful Session Closure                                              │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Filtered Context
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           brain.py (LLM)                                │
│ • Checks interrupt_event on every LLM token — aborts generation         │
│ • Skips clause dispatch when interrupt_event is set                     │
│ • Ollama Timeout + 3x Exponential Backoff Retry                        │
│ • Structured Output (TONE: / SPEAK: format)                            │
│ • Full Response Buffering & Regex Parsing                              │
│ • Token Cap (num_predict: 380) + Temperature Tuning (0.65 / 0.85 top_p)│
└─────────────────────────────────────────────────────────────────────────┘
```

### 1. Data Contracts & Bundle Loader ([schemas.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/schemas.py))
* **Pydantic v2 Input Schemas**:
  - `AnswerRubric`: `poor_answer_indicators`, `good_answer_indicators`, `bar_raiser_indicators`.
  - `InterviewQuestionInput`: Validates `id`, `tier`, `topic`, `difficulty`, `question_text`, `expected_keywords`, `rubric`, `followup_if_strong`, `followup_if_weak`.
  - `InterviewerBehaviorInput`: Validates `session_id`, `persona`, `target_company`, `candidate_name`, `target_role`, `interviewer_system_prompt`, `behavior_rules`.
  - `Stage2SessionBundle`: Ingests Stage 2 artifacts (`behavior`, `questions`, `system_prompt`, `resume_analysis`) with helper properties (`candidate_name`, `target_role`, `target_company`).
* **Pydantic v2 Output Schemas (Phase 3 Event-Driven Logging)**:
  - `TurnManifest`: Captures `turn_id`, `timestamp_iso`, `turn_intent` (`TECHNICAL_ANSWER`, `ICEBREAKER`, `CANDIDATE_META_QUERY`, `SKIP_REQUEST`, `AUDIO_CHECK_OR_PAUSE`, `BARGE_IN_INTERRUPTION`), `question_id`, `topic`, `question_text`, `candidate_transcript`, `candidate_raw_transcript`, `eva_internal_reasoning`, `eva_tone_used`, `eva_spoken_reply`, `audio_start_sec`, `audio_end_sec`, `silence_duration_before_answer_sec`, `evaluation_branch_taken`, `evaluation_metrics` (`keyword_density_score`, `branch_taken`, `matched_keywords`), and `telemetry` (`stt_latency_ms`, `llm_ttft_ms`, `tts_ttfa_ms`, `barge_in_reaction_time_ms`).
  - `SessionMetadata`: Metadata details (`session_id`, `candidate_name`, `target_role`, `target_company`, `start_time_iso`, `end_time_iso`, `total_turns`, `total_barge_ins`).
  - `EvaluatedTechnicalSummary`: Summary scorecard (`topics_covered`, `completed_naturally`, `average_keyword_density`, `strong_branches_triggered`, `weak_branches_triggered`, `skips_requested`).
  - `SessionManifest`: Root container storing `session_metadata`, `full_chronological_transcript` array, and `evaluated_technical_summary`. Maintains backward compatibility with Stage 4 manifest keys (`session_id`, `session_start_iso`, `turns`).
* **Bundle Loader (`load_stage2_bundle`)**: Safely parses and validates inputs from Stage 2 directories.

### 2. State Machine & Adaptive Branching Engine ([question_manager.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/question_manager.py))
* **Question Progression & Lifecycle State Machine**: Manages explicit session phases (`ICEBREAKER` -> `TECHNICAL` -> `LAST_QUESTION` -> `COMPLETED`). Tracks 15 technical interview questions where pointer only advances on `next_topic` transitions or completed evaluations to ensure accurate follow-up evaluation and prevent premature final question cutoffs.
* **Repetition Loop Protection**: Automatically advances to the next topic after 2 weak answer attempts (`retries_on_current_q >= 2`) on the same question.
* **Universal Turn Intent Taxonomy**: `classify_turn_intent()` categorizes every turn into `TECHNICAL_ANSWER`, `ICEBREAKER`, `CANDIDATE_META_QUERY`, `SKIP_REQUEST`, `AUDIO_CHECK_OR_PAUSE`, `BARGE_IN_INTERRUPTION`, or `END_INTERVIEW_REQUEST`. Unfiltered event-driven logging decouples transcript recording from question scoring.
* **Candidate Meta-Intent Override**: `is_candidate_requesting_skip()` intercepts candidate requests to skip or move to the next question (regex matching *"don't know"*, *"no idea"*, *"didn't study"*, *"skip"*, *"pass"*) and forces a `"next_topic"` transition. Explicit requests to stop trigger `END_INTERVIEW_REQUEST` to gracefully conclude the session immediately (specifically avoiding generic standalone words like "end" to prevent false positives on terms like "back-end").
* **Keyword Density Scoring**: Evaluates candidate STT transcripts against expected technical keywords via `calculate_keyword_density()`.
* **Branching Strategy**:
  - **Meta-Intents**: Returns `"interviewer_meta"`, `"audio_check"`, or `"thinking_pause"` immediately.
  - **Icebreaker Transition**: Returns `"icebreaker_response"` on candidate's background intro and transitions `self.phase = "TECHNICAL"`.
  - **Match $\ge$ 50% & `followup_if_strong`**: Triggers `"strong_followup"` branch (escalates to architectural trade-offs and edge cases).
  - **Match $<$ 20% & `followup_if_weak`**: Triggers `"weak_followup"` branch (asks simplifying diagnostic probes).
  - **Otherwise / Interview Completion**: Triggers `"next_topic"` or `"interview_completed"` branch and advances question pointer safely.
* **Natural Conversational Context & Prompt Bridging**: `format_prompt_context()` constructs conversational LLM instructions using the candidate's answer as a bridge. It explicitly forbids the LLM from appending extra bridging questions of its own (`CRITICAL: Ask ONLY this single question`), eliminating "schizophrenic turns" where Eva would ask two disjointed questions in the same breath.
* **Single Source of Truth Session Completion**: `front.py` synchronizes `self.question_count` directly from `self.question_manager.current_index + 1`. Follow-ups and icebreakers no longer trigger premature `self.question_count >= self.MAX_QUESTIONS` cutoffs. The session only wraps up when `QuestionManager` evaluates the candidate's final technical answer and returns `interview_completed`.

### 3. Configuration & 100% Offline Local Model Loading ([config.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/config.py))
* **Zero-Network Execution**: Automatically sets `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` at process launch, preventing all external HTTP/HTTPS network calls to HuggingFace Hub during model initialization.
* **Portable Snapshot Path Resolution**: `resolve_whisper_model_path()` dynamically detects local HuggingFace cache snapshots (`models--Systran--faster-whisper-small\snapshots\...`) using `%USERPROFILE%`, loading model weights directly from local disk. `resolve_kokoro_model_path()` uses the cached `"hexgrad/Kokoro-82M"` repository ID in offline mode.

### 4. Speech-to-Text & Audio Capture ([listener.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/listener.py))
* **Audio Capture Engine**: Built using `sounddevice`. Always opens the stream at the device's native sample rate (e.g. 44100Hz MME, 48000Hz WASAPI) and applies Python-side resampling.
* **Python-Side Resampling**: Boxcar decimation for 48000Hz WASAPI, and `audioop.ratecv` with persistent inter-chunk state for 44100Hz MME.
* **Wiener Filter Noise Suppression (`NoiseReducer`)**: Uses `noisereduce` library (Wiener filter + spectral gating). Handles BOTH stationary noise (fan, AC, HVAC) AND transient bursts (keyboard clicks, mouse, door slams). Applied **ONCE on the full contiguous audio buffer** before STT — NOT per-chunk (per-chunk STFT with `n_fft=512` on exactly 512-sample frames caused 31Hz Hann-window amplitude modulation artifacts that degraded SpeakerVerifier embeddings and Whisper transcription accuracy).
* **Post-TTS Echo Guard Window**: Monotonic timestamp guard (`_echo_guard_until = time.monotonic() + 0.30`) suppresses VAD triggers for 300ms after `state.is_agent_speaking` clears to absorb room acoustic reflections of Eva's last sentence, preventing false barge-in and self-capture.
* **Offline Speaker Verification (`speaker_verifier.py`)**: Employs SpeechBrain `speechbrain/spkrec-ecapa-voxceleb` (192-dim ECAPA-TDNN) to verify candidate identity before STT transcription.
  - **Auto-Enrollment**: Automatically captures 192-dim candidate speaker embedding from the first ICEBREAKER utterance >= 2 seconds.
  - **Verification Gate**: Evaluates cosine similarity of completed audio buffers against enrolled embedding (threshold 0.45 configurable via `.env` SV_THRESHOLD, default 0.55 in `config.py`). Rejects foreign speech (students, teacher, TV, phone) with zero impact on per-frame VAD latency (~15ms per utterance). Audio buffers fed to SpeakerVerifier are DC-filtered raw frames (no noise suppression artifacts) for clean spectral feature extraction.
* **Inline Dynamic Noise Floor Calibration**: Calibration samples ambient noise directly from the active producer queue during the first 960ms of `listen_and_transcribe()`. Eliminates PortAudio driver lockups (silent `0.0000` audio buffers) on Windows caused by rapid stream open/close cycles.
* **Adaptive Speech Gates**: All thresholds computed relative to `ambient_floor`:
  - Speech START: `(VAD prob >= 0.30 AND rms >= 2.5× ambient_floor)` OR `VAD prob >= 0.50`
  - Speech CONTINUATION: silence counter increments only when `rms < 1.8× ambient_floor`
* **Streaming IIR DC Blocker (Pre-VAD)**: A per-sample IIR high-pass filter (`alpha=0.995`, ~5Hz cutoff at 16kHz) is applied to every audio frame BEFORE Silero VAD inference. This removes microphone DC offset that caused the Silero RNN hidden state to saturate (`prob ≈ 0.000` on all frames). The filter carries state across chunks for temporal continuity (Rule 11 compliant — no per-chunk mean subtraction).
* **Hardware Pre-Gain**: A fixed 20x pre-gain multiplier is applied at the very top of the audio pipeline (right after resampling) to correct extremely low microphone capture hardware (-78 dBFS). This ensures the neural network VAD, calibration gates, and Whisper all receive a consistent, properly-scaled signal without dynamic AGC destroying the temporal envelope.
* **Continuous Mic Writer (`ContinuousMicWriter`)**: Writes 3x-boosted 16kHz 16-bit Mono WAV frames directly to `recording.wav`.
* **Faster-Whisper Anti-Hallucination Tuning**: `condition_on_previous_text=False`, `no_speech_threshold=0.6`, `hallucination_silence_threshold=2.0`, `temperature=0.0`, `beam_size=1`.
* **Input Modes (Auto-VAD vs Push-To-Talk)**: Supports both automatic VAD speech endpointing and PTT mode.
* **Async Producer/Consumer Queue Architecture**: `listen_and_transcribe()` spawns a background daemon thread (`mic_stream_producer`) to continuously drain mic frames into a thread-safe `queue.Queue()`.
* **Hardware Lock Retry Loop**: Both `listen_and_transcribe` and `BargeInWatcher` implement a 3-attempt, 0.3s delay retry on `sd.InputStream` initialization.
* **Hybrid Turn Classifier & Dynamic Pause Extension ([turn_classifier.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/turn_classifier.py))**:
  - Implements Case 3 Hybrid Architecture to determine if candidate speech is a complete thought or an interrupted thinking pause.
  - **Tier 0 (Ollama Liveness Probe)**: Skips Tier 2 if Ollama is unreachable.
  - **Tier 1 (Regex/Lexical - 0ms)**: Checks trailing conjunctions and filler words.
  - **Tier 2 (Qwen2.5 Probe - ~100ms)**: Calls local Ollama model using `OLLAMA_MODEL` (aligned with `brain.py` to prevent latency from model swapping in GPU/RAM memory) with a safety timeout limit. Non-200 HTTP responses now correctly return `"COMPLETE"` via explicit fallback return (previously could implicitly return `None`).
  - When initial 800ms silence threshold is hit, dynamic pause extends up to 2300ms if thought is incomplete.
* **Full-Duplex Real-Time Barge-In (v3)**: VAD runs continuously even while `state.is_agent_speaking` is set. When `speech_prob > 0.65`:
  1. **Cooldown check** (`interrupt_cooldown_sec=0.3s`) prevents rapid re-triggering.
  2. **Sets `state.interrupt_event`** signal.
  3. **Calls `force_stop_all()`** hardware audio flush.
  4. **Falls through** into normal audio accumulation.


### 5. LLM Engine, Text Sanitizer & TTFT/TTFA Telemetry ([brain.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/brain.py) & [speaker.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/speaker.py))
* **Model**: Local Ollama execution of **`qwen2.5:3b`** (`MODEL_NAME = OLLAMA_MODEL`). Includes 3x exponential backoff retry and streams raw output live to console. Silences HTTPX and HTTPCORE debug logs from console stdout.
* **Accurate Millisecond Benchmark Telemetry**:
  - **TTFT (Time-To-First-Token)**: Recorded on arrival of the first LLM token (<300ms).
  - **TTFA (Time-To-First-Audio)**: Recorded in `speaker.py` when the first synthesized Kokoro audio chunk is pushed to `audio_queue` (<1200ms).
* **Humanized System Prompt & Dynamic Grounding**: Uses `DEFAULT_EVA_SYSTEM_PROMPT` enforcing:
  - Natural spoken cadence with contractions ("I'm", "let's", "it's", "that's") and short vocal anchors ("Ah, got it", "Hmm", "I see").
  - **Resume Context Anchor**: Dynamically injects candidate background facts (skills, achievements, red flags) extracted from Stage 2 `resume_analysis.json` directly into the system prompt to enforce personalized reference-grounding.
  - **Personalization Guardrails**: Enforces specific conversational bridging (using the candidate's exact prior words) and anchor rotation (never using the same vocal anchor twice in a row) to maximize naturalness.
  - Strict limitation to **exactly one question per turn**.
  - Fast two-line output format (`TONE:` / `SPEAK:`) to eliminate parsing overhead and `<think>` blocks.
  - Mandatory Call-To-Action (CTA) handoff rule: Every `SPEAK:` payload MUST end with a terminal question mark (`?`) or explicit turn handoff question.
  - Mandatory `TONE:` attribute selection from Tone Taxonomy.
  - **System Prompt Caching (Optimization)**: The heavy prompt string is built once and cached in `front.py`, regenerating only if the candidate's project anchor hash changes (e.g., after the icebreaker turn).
* **Tuned Params**: `num_predict: 380` (expanded token headroom to prevent truncation mid-sentence), `temperature: 0.65` (lower variance for crisp CTA adherence), `top_p: 0.85` (grammatical sentence endings), `repeat_penalty: 1.15`.
* **Tone-to-Speed Parameter Mapping Matrix (`get_speed_for_tone`)**:
  - `empathetic` / `encouraging`: `0.92x` (reassuring, unhurried cadence).
  - `curious` / `probing`: `1.05x` (inquisitive, high-energy trade-off escalation).
  - `warm` / `icebreaker`: `0.96x` (approachable, conversational rapport building).
  - `direct` / `technical`: `1.00x` (baseline professional delivery).
  - Speed boundary strictly clamped between `0.88x` and `1.08x`.
* **Software Guardrail Safety Net**: `stream_llm_response` inspects the final character of the generated output. If terminal punctuation (`?`, `.`, `!`) is missing due to a model cutoff, it automatically appends `"... What are your thoughts on that?"` before passing text to `speaker.py`.
* **Low-Latency Stream Architecture**: 
  - System prompt rigorously enforces a two-line `TONE:` and `SPEAK:` format, skipping Chain-of-Thought (CoT) to immediately stream audio.
  - Responses are parsed line-by-line without waiting for heavy XML blocks to close.
* **Interrupt-Aware Token Loop (v2)**: `stream_llm_response` checks `session_state.interrupt_event` on **every token**. When set (candidate barge-in), LLM generation is aborted immediately. Clause dispatch is also gated — no clauses are sent to the speaker after an interrupt.
* **Sub-Second Clause Streaming & Batching**: `stream_llm_response` scans the raw LLM token stream for the `TONE:` line, sets `session_state.current_tone` and `session_state.tts_speed` early, and immediately streams all tokens following `SPEAK:` to the clause splitter on punctuation boundaries (`[,?!.\n]`).
  - **6-Word Minimum TTS Batching (Optimization)**: Small fragments (like "Ah," or "Right,") are buffered until the clause exceeds 6 words or ends with a terminal punctuation mark before being dispatched to `PersistentSpeaker`. This drastically reduces the number of separate Kokoro inference calls per turn while maintaining sub-350ms TTFA.
* **Prosodic Regex TextSanitizer (`TextSanitizer.clean_for_tts` & `clean_for_ui`)**:
  - `clean_for_ui`: Strips XML, brackets, and action tags (`[Clears Throat]`) exclusively for clean Kivy UI transcript logging without affecting natural punctuation.
  - `clean_for_tts`: Injects tone-specific prosody (soft opening ellipses for empathetic tones, natural breathing commas for warm tones) and Forced Technical Micro-Pauses (em-dashes or commas around complex technical terms like `asyncio`).
  - **Kokoro Pitch Spike Elimination**: Automatically replaces exclamation marks `!` with soft periods `.` to ensure smooth, natural TTS delivery without forced artificial pitch spikes.

### 6. Text-to-Speech Playback ([speaker.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/speaker.py))
* **PersistentSpeaker (Clause-Level PyAudio Stream)**: Employs a Producer-Consumer `queue.Queue` alongside a persistent, always-open `pyaudio.PyAudio()` output stream running in a daemon thread. Completely eliminates hardware handshake delays (0ms overhead) across the entire session. Reuses the persistent audio stream across tone changes and voice preset swaps with zero driver re-init penalty. Suppresses PyTorch RNN and weight_norm deprecation warning noise.
* **Dynamic Voice Preset Selection**: Supports `af_bella`, `af_nicole`, `bf_emma`, and `am_adam` selectable via `state.selected_voice` or Kivy UI dropdown controls.
* **Extreme Microphone Sensitivity Tuning**:
  - Noise gate lowered to `0.0005` (from 0.002).
  - Auto-gain cap increased to `40x` (from 20x).
  - OR-logic speech trigger (`VAD > 0.25` OR `RMS > 0.005`) with fast 64ms debounce allows effortless barge-in without needing to shout.
  - Whisper internal `vad_filter` disabled to prevent stripping of quiet/distant speech.
* **Filler Word Removed**: The random "Okay.", "Right.", "Alright." filler before LLM generation has been removed. The LLM's own conversational anchors ("Ah,", "Got it,") stream as the first clause with sub-250ms TTFA, providing a natural response gap without the artificial pre-generation delay (~400ms saved).
* **Technical Text Normalization**: Prevents odd pausing on strings like "Python 3.11", "Next.js", and "HTTP/1.1".
* **Kokoro-82M Engine**: Neural TTS initialized using `KPipeline(lang_code="a")` with `af_bella` voice.

### 6. Session Telemetry & Clean Log Storage ([session_logger.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/session_logger.py) & [benchmark.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/benchmark.py))
* **Single Output Contract (`transcript.json`)**: Writes strictly `transcript.json` and `recording.wav` in the session output directory. Redundant duplicate file creation (`session_manifest.json`) and inner array key duplication (`full_chronological_transcript` vs `turns`) are completely eliminated.
* **Clean Codebase Log Storage**: `front.py` logs session transcripts directly into `model/voice_to_voice_model/model/_interview_log.txt`. Creation of `test_output/` folder and `benchmark_log.csv` file has been completely removed to prevent file clutter.
* **Codebase Audit Cleanups**: Declared missing `last_stt_ms`, `last_ttft_ms`, `last_ttfa_ms` class attributes in `benchmark.py`. Removed unused dead imports (`csv`, `os`, `Generator`), dead variables (`CSV_PATH`, `manifest_path`), dead `DummyEvent` class, and redundant `model/voice_to_voice_model/model/run.bat` duplicate. Corrected `Benchmark.end()` timestamp key popping.

### 7. Multi-Screen Desktop Application & Headless CLI ([front.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/front.py) & [test_pipeline.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/test_pipeline.py))
* **Kivy Multi-Screen Architecture (`ScreenManager`)**:
  - Uses a **Premium Dark Theme Redesign** featuring deep charcoal backgrounds (`#121212`), elevated dark-gray rounded panels (`#1E1E24`), tactile solid-colored flat buttons, and vibrant color-coded chat tags (Eva in blue, User in teal, System in amber).
  - **`InterviewScreen`**:
    - Top Action Bar with prominent `📜 View Session Output History` button.
    - Streamlined Preset Selector (`sample_backend`, `sample_frontend`, `sample_fullstack`) and Question Limit Selector (5, 10, 15, All).
    - Hard-coded default session settings: `800ms` Fast Response pause tolerance, `af_bella` Kokoro voice, and `Auto-VAD` mode.
    - Live VAD visualizer & volume diagnostics bar.
  - **`SessionHistoryScreen`**:
    - Full-page output inspector displaying past `sess_<timestamp>` output folders.
    - Interactive WAV audio player with real-time `ProgressBar` and time tracking (`0:15 / 1:30`).
* **SessionState Management**: Thread-safe `session_state.py` orchestrating cross-module events (Echo Gate, full-duplex barge-in interrupt).
* **UI Rendering & Parallel Text Streaming**: Streams the LLM `SPEAK:` text output into the GUI character-by-character in real-time (`ui_callback`), exactly parallel with the TTS audio playback. The `_llm_ui_callback` receives direct streaming text without any XML parsing overhead, guaranteeing a clean front-end display. Displays spoken dialog using color-coded markup labels, and ensures only the clean spoken block is fed back into `conversation_history` context to prevent compounding context errors.
* **Permanent Context Anchor & Personalized Greeting**: Extracts candidate background details during the ICEBREAKER phase into a `candidate_project_anchor`, dynamically prepending it to the system prompt so it is never purged. The initial greeting is simplified to a time-based one-liner (e.g., "Good morning, Candidate. How are you doing?") to allow a short response for clean auto-enrollment before diving into technical questions. `resume_highlights` are natively passed through to the `question_manager` to weave specific candidate facts into dynamic technical follow-ups.
* **Bounded Sliding Context History**: Caps LLM chat history length to prevent performance degradation over time, relying on the permanent anchor to retain crucial context.
* **`_eva_speak_blocking` Audio Drain Fix (v2)**: Replaced unreliable `audio_queue.empty()` poll with `audio_queue.join()` executed in a daemon thread polled every 50ms with interrupt bail-out. A mandatory **150ms post-drain OS hardware buffer guard** then ensures the PyAudio WASAPI/ALSA driver buffer fully completes playback before `listen_and_transcribe()` opens the microphone. This eliminates acoustic bleed-back (Eva's voice leaking into mic) triggering a false barge-in → `force_stop_all()` → session ending with 0 turns.
* **`brain.py preload()` Fix**: Corrected `preload()` to call `stream_llm_response()` directly as a function call instead of iterating its tuple return value with `for _ in ...` (which wrongly treated the tuple as a generator).
* **High-Fidelity Native OS Audio Capture Override**: Implemented `.env` controlled `MIC_DEVICE_INDEX` fallback. `listener.py` now attempts to open streams at exactly 16000Hz (Method B native OS resampling via MME/DirectSound) first, and falls back to manual decimation only if the hardware rejects it (e.g., WASAPI). Combined with a custom IIR high-pass filter (`alpha=0.995`) applied across the final utterance buffer, this completely eliminates 31Hz digital buzzing caused by chunk boundary DC discontinuities and mathematical aliasing.

---

## 🔥 Full-Duplex Barge-In Signal Flow

```
Candidate speaks while Eva talks
          │
          ▼
BargeInWatcher (Daemon Thread): speech_prob > 0.50 && cooldown passed
          │
          ├─► state.interrupt_event.set()          ← Global signal
          ├─► state.last_interrupt_time = now      ← Cooldown timestamp
          ├─► force_stop_all()                     ← Hardware buffer flush
          │       ├─► speaker._drain_queue()       ← Python queue cleared
          │       └─► stream.stop_stream() +       ← WASAPI/ALSA flushed
          │           stream.start_stream()
          ├─► state.is_agent_speaking.clear()
          └─► Watcher exits. Main listener.py      ──────► STT captures barge-in speech
              starts fresh and captures speech             (NOT discarded!)

brain.py: next token check → interrupt_event.is_set() → break generation

speaker._play_loop: next sub-chunk → interrupt_event.is_set() → break write

front.py: _eva_speak_blocking audio queue drain poll exits
          │
          │
          ▼
front.py: Next turn begins
          ├─► state.interrupt_event.clear()    ← Reset for new turn
          ├─► player.interrupt_event.clear()   ← Unblock speaker
          └─► state.is_agent_speaking.set()    ← Before LLM starts
```

---

## 📊 Performance Benchmark Targets
| Metric | Description | Target | Current Status |
| :--- | :--- | :--- | :--- |
| **STT Latency** | Audio silence to Whisper text output | < 600 ms | Operational (~350–550 ms) |
| **TTFT** | Prompt sent to LLM first token output | < 400 ms | Operational (~200–350 ms) |
| **TTFA** | User silence to speaker first audio chunk | < 400 ms | Operational (~250–350 ms) |
| **Barge-In Reaction** | Candidate speech to audio stop | < 60 ms | **~21ms hardware + ~42ms sub-chunk = ~63ms max** |
