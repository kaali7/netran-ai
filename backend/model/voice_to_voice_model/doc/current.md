# Netran AI Voice-to-Voice: Current Implementation & System Architecture

## 📌 Executive Summary
The Netran AI Voice-to-Voice backend and desktop application run a real-time, low-latency cascaded voice processing pipeline comprising **Neural Voice Activity Detection (Silero VAD)**, **Speech-to-Text (Faster-Whisper)**, **Dynamic State Machine & Adaptive Branching (QuestionManager)**, **Streaming LLM Reasoning (Ollama Qwen2.5:1.5B)** with **Regex TextSanitizer**, and **Text-to-Speech (Kokoro-82M)**, integrated into a multi-screen dark-themed **Kivy Desktop GUI**.

Additionally, Stage 3 ingests Stage 2 session artifact bundles (`interview_questions.json`, `interviewer_behavior.json`, `system_prompt.txt`, `resume_analysis.json`) via `schemas.py` Pydantic contracts and exports consolidated session outputs (`recording.wav` + `session_manifest.json`) for downstream Stage 4 post-session evaluation engines.

---

## 🏗️ Core Architecture & Component Breakdown

```
┌────────────────────────────────────────────────────────────────────────┐
│                        STAGE 2 ARTIFACT BUNDLE                         │
│  (test/input/sample_backend/ or backend/sessions/<session_id>/)       │
│  • interview_questions.json  • interviewer_behavior.json             │
│  • system_prompt.txt         • resume_analysis.json                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Ingested via schemas.py
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     STAGE 3 VOICE EXECUTION ENGINE                     │
│                                                                        │
│   ┌───────────────────────┐             ┌──────────────────────────┐   │
│   │   listener.py (STT)   │             │   QuestionManager        │   │
│   │   • Faster-Whisper    │────────────►│   • 15-Question Sequence │   │
│   │   • Technical Vocab   │  Transcript │   • Keyword Scoring      │   │
│   └───────────────────────┘             │   • Branch Selection     │   │
│                                         └─────────────┬────────────┘   │
│                                                       │ Context        │
│                                                       ▼                │
│   ┌───────────────────────┐             ┌──────────────────────────┐   │
│   │   speaker.py (TTS)    │             │   brain.py (LLM Engine)  │   │
│   │   • Kokoro-82M        │◄────────────│   • Qwen2.5:1.5B         │   │
│   │   • Clean Audio Output│ Clean Text  │   • TextSanitizer Regex  │   │
│   └───────────────────────┘             └──────────────────────────┘   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Output Telemetry
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     OUTPUT SESSION ARTIFACTS                           │
│  (backend/sessions/<session_id>/ or test/output/sess_<timestamp>/)     │
│  • recording.wav          (Gain-boosted continuous mic audio)          │
│  • session_manifest.json  (Turn-by-turn latency & scoring manifest)    │
└────────────────────────────────────────────────────────────────────────┘
```

### 1. Data Contracts & Bundle Loader ([schemas.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/schemas.py))
* **Pydantic v2 Input Schemas**:
  - `AnswerRubric`: `poor_answer_indicators`, `good_answer_indicators`, `bar_raiser_indicators`.
  - `InterviewQuestionInput`: Validates `id`, `tier`, `topic`, `difficulty`, `question_text`, `expected_keywords`, `rubric`, `followup_if_strong`, `followup_if_weak`.
  - `InterviewerBehaviorInput`: Validates `session_id`, `persona`, `target_company`, `candidate_name`, `target_role`, `interviewer_system_prompt`, `behavior_rules`.
  - `Stage2SessionBundle`: Ingests all 4 Stage 2 artifacts (`behavior`, `questions`, `system_prompt`, `resume_analysis`).
* **Pydantic v2 Output Schemas**:
  - `TurnManifest`: Captures `turn_id`, `question_id`, `topic`, `question_text`, `candidate_transcript`, `audio_start_sec`, `audio_end_sec`, `stt_latency_ms`, `ttft_ms`, `evaluation_branch_taken` (`strong_followup` | `weak_followup` | `next_topic`).
  - `SessionManifest`: Root container storing metadata (`session_id`, `session_start_iso`, `total_turns`) and `turns`.
* **Bundle Loader (`load_stage2_bundle`)**: Safely parses and validates inputs from Stage 2 directories.

### 2. State Machine & Adaptive Branching Engine ([question_manager.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/question_manager.py))
* **Question Progression**: Tracks sequence of 15 technical interview questions.
* **Keyword Density Scoring**: Evaluates candidate STT transcripts against expected technical keywords.
* **Branching Strategy**:
  - **Match $\ge$ 50% & `followup_if_strong`**: Triggers `"strong_followup"` branch (escalates to architectural trade-offs and edge cases).
  - **Match $<$ 20% & `followup_if_weak`**: Triggers `"weak_followup"` branch (asks simplifying diagnostic probes).
  - **Otherwise**: Triggers `"next_topic"` branch and advances question pointer (`current_index += 1`).

### 3. Speech-to-Text & Audio Capture ([listener.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/listener.py))
* **Audio Capture Engine**: Built using `sounddevice` running at 16kHz single-channel `float32`.
* **Per-Frame DC Offset + Auto-Gain Pipeline**: Peak auto-gain up to **50x boost targeting 90% peak**, resolving quiet recordings on low-gain Windows microphone arrays.
* **Continuous Mic Writer (`ContinuousMicWriter`)**: Writes gain-boosted 16kHz 16-bit Mono WAV frames directly to `recording.wav`.
* **Silero VAD v3 + Faster-Whisper**: Speech endpointing and real-time STT transcription.

### 4. LLM Engine & Text Sanitizer ([brain.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/brain.py))
* **Model**: Local Ollama execution of `qwen2.5:1.5b`.
* **Regex TextSanitizer (`TextSanitizer.clean_for_tts`)**:
  - Strips bracketed tokens like `[Clears Throat]`, `(Sighs)` using `r'\[.*?\]|\(.*?\)'`.
  - Strips markdown formatting like `*action*`, `**bold**` using `r'\*+'`.
  - Normalizes whitespace before passing text to Kokoro TTS.

### 5. Text-to-Speech Playback ([speaker.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/speaker.py))
* **Kokoro-82M Engine**: Neural TTS initialized using `KPipeline(lang_code="a")` with `af_bella` voice. Direct output to WASAPI via `sounddevice.play()`.

### 6. Session Manifest & Telemetry ([session_logger.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/session_logger.py))
* **Unified Output Contract**: Writes strictly `session_manifest.json` and `recording.wav` in the session output directory. Redundant `transcript.json` and duplicate `continuous_mic_input.wav` files are eliminated.

### 7. Multi-Screen Desktop Application & Headless CLI ([front.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/front.py) & [test_pipeline.py](file:///c:/kali/product/netran%20ai/backend/model/voice_to_voice_model/model/test_pipeline.py))
* **Kivy Multi-Screen Architecture (`ScreenManager`)**:
  - **`InterviewScreen`**:
    - Top Action Bar with prominent `📜 View Session Output History` button.
    - Preset Selector & LLM/Calibration mode toggles.
    - Selectable Question Limit Spinner (5, 10, 15, All Available Questions) with auto-end and output session generation.
    - Live VAD visualizer & volume diagnostics bar.
    - Non-overlapping, clean 4-button control bar (`Start Interview`, `Done Speaking`, `Final Stop & Output`, `Restart Session`).
  - **`SessionHistoryScreen`**:
    - Full-page output inspector displaying past `sess_<timestamp>` output folders.
    - Left-pane header `⬅️ Back` button for returning to the live interview panel.
    - Interactive WAV audio player with real-time `ProgressBar` and time tracking (`0:15 / 1:30`).
    - Pixel-perfect text wrapping (`text_size: self.width - 32, None`), zero clipping, and color-coded telemetry and dialogue transcripts.
* **Headless CLI Test Harness (`test_pipeline.py`)**: Automated test execution.

---

## 📊 Performance Benchmark Targets
| Metric | Description | Target | Current Status |
| :--- | :--- | :--- | :--- |
| **STT Latency** | Audio silence to Whisper text output | < 600 ms | Operational (~350–550 ms) |
| **TTFT** | Prompt sent to LLM first token output | < 400 ms | Operational (~200–350 ms) |
| **TTFA** | User silence to speaker first audio chunk | < 1200 ms | Operational (~800–1100 ms) |
