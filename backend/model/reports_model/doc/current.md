# Stage 4 — Evaluation & Report Generation Engine (Current Status)

**Status:** ✅ **COVERED & OPERATIONAL (GROQ + WAV2VEC2 LOCAL UPGRADE)**  
**Subsystem Directory:** `backend/model/reports_model/`  
**Last Updated:** October 15, 2026  

---

## 1. Subsystem Overview

Stage 4 is the post-session analytics and synthesis subsystem of Netran AI. It ingests:
- `continuous_mic_input.wav` / `recording.wav`: Raw continuous audio recording from Stage 3.
- `transcript.json` / `session_manifest.json`: Per-turn millisecond timing telemetry from Stage 3.
- `sample_resume.txt` / `sample_resume.json`: Candidate resume context (Stage 1/2 Grounding).
- `sample_rubric.json` / `sample_job_detail.json`: Job rubric and pillar requirements (Stage 1 Grounding).

### Architecture Transition (October 2026 Upgrade)
The previous slow Google Gemini multimodal audio upload pipeline was completely overhauled to resolve HTTP upload latency and 429 quota exhaustion. The updated Stage 4 architecture leverages:
1. **Deterministic Vocal Delivery Analytics (`audio_metrics.py`)**: Instant pure-Python calculation of speaking rate (WPM), speech coverage ratio, silence duration, pause counts (>0.7s), and filler word density directly from timestamps.
2. **Local CPU Speech Emotion Recognition (`emotion_service.py`)**: [`superb/wav2vec2-base-superb-er`](https://huggingface.co/superb/wav2vec2-base-superb-er) (~360MB) executed on **CPU** with **0 MB VRAM** overhead, classifying turns into `{Calm, Confident, Uncertain, Stressed}` in ~150ms without competing with Faster-Whisper or Kokoro-82M on the 6GB RTX 4050.
3. **High-Speed Technical Answer Intelligence (`answer_evaluator.py`)**: Powered by Groq (`openai/gpt-oss-120b`) with sub-500ms response times, and resilient automatic fallback to local Ollama (`qwen2.5:3b`) and offline deterministic rule heuristics.
4. **Instant End-to-End Latency**: Generates complete executive scorecards, pillar breakdowns, and audio delivery roadmaps in **~2 to 4 seconds total**.

---

## 2. Component Architecture & Test Harness Directory Layout

```
backend/model/reports_model/
├── doc/
│   ├── current.md              # Stage 4 technical implementation status
│   └── prd.md                  # Stage 4 Product Requirements Document
├── test/                       # Stage 4 standardized test harness directories
│   ├── input/                  # Stage 3 preset input sessions (sample1/)
│   └── output/                 # Generated session report artifacts (sess_<timestamp>/)
└── model/
    ├── audio_slicer.py         # Non-destructive WAV slicing utility
    ├── audio_metrics.py        # Deterministic WPM, pause, silence & filler analytics
    ├── emotion_service.py      # Local CPU Wav2Vec2 speech emotion & confidence classifier
    ├── answer_evaluator.py     # Groq + Ollama technical answer intelligence & combine synthesis
    ├── config.py               # Configuration loader (Groq, Ollama, Wav2Vec2, Gemini)
    ├── schemas.py              # Pydantic v2 models for report payload & evaluation outputs
    ├── pipeline.py             # Master orchestrator & artifact renderer (JSON + Markdown)
    ├── prompts.py              # Centralized dynamic system prompts
    ├── gemini_evaluator.py     # Legacy Gemini multimodal evaluator (backward compatibility)
    ├── report_builder.py       # Backward compatibility alias for pipeline.py
    ├── report_schema.py        # Backward compatibility alias for schemas.py
    ├── test_pipeline.py        # CLI headless verification runner with dynamic interactive menu
    └── front.py                # Interactive Kivy desktop UI for testing
```

---

## 3. Evaluation Flow & Pipeline

```
  continuous_mic_input.wav + transcript.json + Context Files (Resume/Rubric)
                          │
                          ▼
              ┌──────────────────────┐
              │   audio_slicer.py    │
              └───────────┬──────────┘
                          │ Slices turn_XX.wav clips
                          ▼
          ┌──────────────────────────────────┐
          │           pipeline.py            │
          │ ┌──────────────┐ ┌─────────────┐ │
          │ │ Audio Branch │ │Tech Branch  │ │
          │ │ audio_metrics│ │(Groq Cloud  │ │
          │ │      +       │ │/Ollama Local│ │
          │ │emotion_servce│ │Evaluator)   │ │
          │ └──────┬───────┘ └──────┬──────┘ │
          │        └───────┬────────┘        │
          │                ▼                 │
          │         Combine Branch           │
          │  (Progressive Cache Saving to    │
          │         turn_cache.json)         │
          └────────────────┬─────────────────┘
                           │ CandidateReportPayload
                           ▼
              ┌──────────────────────┐
              │  pipeline.py         │
              └───────────┬──────────┘
                          │ Writes artifacts
                          ▼
    backend/model/reports_model/test/output/sess_<timestamp>/ (or backend/data/sessions/<id>/)
    ├── report.json
    └── evaluation_summary.md
```

---

## 4. Key Artifacts & Enhanced Executive Payload

Inside `test/output/sess_<timestamp>/` (or active `backend/data/sessions/<session_id>/`):
1. `report.json`: Machine-readable Pydantic JSON payload for dashboard rendering and analytics storage. Features:
   - **Precision Telemetry (`TurnTelemetry`):** Deterministic latency ms, clip duration sec, and STT Whisper hallucination detection flags.
   - **Behavioral Red Flags (`BehavioralFlag`):** Top-level array capturing critical events (e.g., session abort requests, severe acoustic-STT discrepancies).
   - **Candidate Upskilling Roadmap (`CandidateFeedback`):** Key strengths, primary growth areas, and recommended study topics.
   - **Context Fallback Grounding:** Automatic fallback notice when candidate resume or Stage 1 rubric is omitted.
2. `evaluation_summary.md`: Human-readable Markdown summary with scorecards, pillar breakdowns, integrity alerts, growth roadmaps, and turn-by-turn telemetry notes.
3. `turn_cache.json`: Progressively saved cache of `AudioBranchOutput` and `TechnicalBranchOutput` models. Enables instantaneous resume on failure and live GUI streaming during generation.
4. `turn_XX.wav`: Per-turn sliced audio clips.

---

## 5. Running & Verification Commands

- **Headless CLI Test Pipeline (Interactive Session Picker):**
  ```cmd
  .\.venv\Scripts\python.exe -m model.reports_model.model.test_pipeline
  ```

- **Kivy Desktop Test UI:**
  ```cmd
  .\.venv\Scripts\python.exe -m model.reports_model.model.front
  ```

- **Interactive System Launcher:**
  Run `run.bat` at the backend root and select Option `5` (Stage 4), then pick mode `1` (Kivy) or `2` (CLI).
